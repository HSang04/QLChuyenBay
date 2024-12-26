from datetime import timedelta

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request, redirect, flash, url_for, session, current_app
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf import FlaskForm

from cbapp import app, dao, login, db, create_db
from cbapp.dao import get_user_info
from cbapp.forms import ChangePasswordForm, ChangeInfoForm
from cbapp.models import KhachHang, NhanVien, Ve, LichSuGiaoDich

from wtforms.fields.simple import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Email, Length, EqualTo, DataRequired
from sqlalchemy import asc


@app.route('/')
def index():
    return redirect('/trangchu')



@app.route('/login', methods=['GET', 'POST'])
def login_process():
    err_msg = None
    if request.method == 'POST':
        tai_khoan = request.form['taiKhoan']
        mat_khau = request.form['matKhau']

        user = dao.auth_user(taiKhoan=tai_khoan, matKhau=mat_khau)

        if user:
            login_user(user)

            app.logger.info(f"Login successful! Current user: {current_user}")
            app.logger.info(f"User ID: {current_user.get_id()}")
            app.logger.info(f"Username: {current_user.get_username()}")
            app.logger.info(f"User Email: {current_user.email}")

            if isinstance(user, KhachHang):
                session['user_type'] = 1
            elif isinstance(user, NhanVien):
                session['user_type'] = 2

            next = request.args.get('next')

            if isinstance(user, NhanVien):
                if user.vaiTro == VaiTro.BANVE:
                    return redirect('/banve')
                elif user.vaiTro == VaiTro.QUANTRI:
                    return redirect('/admin')
            elif isinstance(user, KhachHang):
                return redirect(next if next else '/trangchu')
        else:
            err_msg = "Sai tài khoản hoặc mật khẩu."

    return render_template('login.html', err_msg=err_msg)

@app.route('/logout')
def logout():
    logout_user()
    session.pop('user_type', None)
    flash('Bạn đã đăng xuất thành công!', 'success')
    return redirect('/login')

@app.route('/dangky', methods=['GET', 'POST'])
def dang_ky():
    form_data = {}
    if request.method == 'POST':

        form_data['hoVaTen'] = request.form.get('hoVaTen')
        form_data['email'] = request.form.get('email')
        form_data['soDienThoai'] = request.form.get('soDienThoai')
        form_data['taiKhoan'] = request.form.get('taiKhoan')
        form_data['cccd'] = request.form.get('cccd')
        matKhau = request.form.get('matKhau')
        xacNhanMatKhau = request.form.get('xacNhanMatKhau')


        if matKhau != xacNhanMatKhau:
            flash("Mật khẩu và xác nhận mật khẩu không trùng khớp. Vui lòng nhập lại.", "danger")
            form_data.pop('matKhau', None)
            form_data.pop('xacNhanMatKhau', None)
            return render_template('dangky.html', form_data=form_data)


        khach_hang_ton_tai = KhachHang.query.filter(
            (KhachHang.taiKhoan == form_data['taiKhoan']) |
            (KhachHang.email == form_data['email']) |
            (KhachHang.soDienThoai == form_data['soDienThoai']) |
            (KhachHang.cccd == form_data['cccd'])
        ).first()

        if khach_hang_ton_tai:
            if KhachHang.query.filter_by(taiKhoan=form_data['taiKhoan']).first():
                flash("Tài khoản đã tồn tại. Vui lòng nhập tài khoản khác.", "danger")
                form_data.pop('taiKhoan', None)

            if KhachHang.query.filter_by(email=form_data['email']).first():
                flash("Email đã tồn tại. Vui lòng nhập email khác.", "danger")
                form_data.pop('email', None)

            if KhachHang.query.filter_by(soDienThoai=form_data['soDienThoai']).first():
                flash("Số điện thoại đã tồn tại. Vui lòng nhập số khác.", "danger")
                form_data.pop('soDienThoai', None)

            if KhachHang.query.filter_by(cccd=form_data['cccd']).first():
                flash("CCCD đã tồn tại. Vui lòng nhập CCCD khác.", "danger")
                form_data.pop('cccd', None)

            return render_template('dangky.html', form_data=form_data)

        khach_hang_moi = KhachHang(
            hoVaTen=form_data['hoVaTen'],
            email=form_data['email'],
            soDienThoai=form_data['soDienThoai'],
            taiKhoan=form_data['taiKhoan'],
            cccd=form_data['cccd'],
            active=True
        )
        khach_hang_moi.set_password(matKhau)  # Mã hóa mật khẩu

        # Lưu vào cơ sở dữ liệu
        try:
            db.session.add(khach_hang_moi)
            db.session.commit()
            flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
            return redirect(url_for('login_process'))
        except Exception as e:
            db.session.rollback()
            flash("Có lỗi xảy ra. Vui lòng thử lại.", "danger")

    return render_template('dangky.html', form_data=form_data)


@login.user_loader
def load_user(user_id):
    user_type = session.get('user_type')

    if user_type == 2:  # Nhân viên
        user = dao.get_nhan_vien_by_id(user_id)
        if user:
            app.logger.info(f"Loaded NhanVien: {user}")
            return user

    elif user_type == 1:  # Khách hàng
        user = dao.get_khach_hang_by_id(user_id)
        if user:
            app.logger.info(f"Loaded KhachHang: {user}")
            return user
    return None

#
@app.route('/banve')
def banve():
    if isinstance(current_user, NhanVien) and current_user.vaiTro.__eq__(VaiTro.BANVE):
        return render_template('banve.html')
    return redirect('/login')

@app.route('/trangchu')
def trangchu():

    sanBays = SanBay.query.all()
    sanBayDi = request.args.get('sanBayDi')
    sanBayDen = request.args.get('sanBayDen')
    ngayDi = request.args.get('ngayDi')

    chuyenBays = ChuyenBay.query.join(TuyenBay).filter(
        (TuyenBay.maSanBayDi == sanBayDi if sanBayDi else True) &
        (TuyenBay.maSanBayDen == sanBayDen if sanBayDen else True) &
        (ChuyenBay.gioDi >= datetime.strptime(ngayDi, '%Y-%m-%d') if ngayDi else True)
    ).all()
    now = datetime.now()
    chuyenBayDeXuat = ChuyenBay.query.filter(ChuyenBay.gioDi >= now).order_by(ChuyenBay.gioDi).all()
    return render_template('trangchu.html', sanBays=sanBays, chuyenBays=chuyenBays,
                           chuyenBayDeXuat=chuyenBayDeXuat)


@app.route('/tim-chuyen-bay', methods=['GET', 'POST'])
def tim_chuyen_bay():
    sanBays = SanBay.query.all()
    chuyenBays = []

    if request.method == 'POST':
        sanBayDi = request.form['sanBayDi']
        sanBayDen = request.form['sanBayDen']
        ngayDi = request.form['ngayDi']


        session['form_data'] = {
            'sanBayDi': sanBayDi,
            'sanBayDen': sanBayDen,
            'ngayDi': ngayDi
        }


        current_time = datetime.now()
        min_time = current_time + timedelta(hours=12)
        chuyenBays = ChuyenBay.query.join(TuyenBay).filter(
            TuyenBay.maSanBayDi == sanBayDi,
            TuyenBay.maSanBayDen == sanBayDen,
            ChuyenBay.gioDi >= min_time
        ).order_by(asc(ChuyenBay.gioDi)).all()

    form_data = session.get('form_data', {})
    return render_template('timchuyenbay.html', sanBays=sanBays, chuyenBays=chuyenBays, data=form_data)

@app.route('/dat_ve/<int:ma_chuyen_bay>', methods=['GET', 'POST'])
def dat_ve(ma_chuyen_bay):
    if not current_user.is_authenticated:
        flash('Vui lòng đăng nhập trước khi đặt vé.', 'warning')
        return redirect(url_for('login_process'))

    chuyenBay = ChuyenBay.query.get_or_404(ma_chuyen_bay)

    gheThuongGia = Ghe.query.filter_by(maChuyenbay=chuyenBay.maChuyenBay, hangGhe='ThuongGia').all()
    ghePhoThong = Ghe.query.filter_by(maChuyenbay=chuyenBay.maChuyenBay, hangGhe='PhoThong').all()

    soGheThuongGiaConLai = len([ghe for ghe in gheThuongGia if ghe.trangThai == False])
    soGhePhoThongConLai = len([ghe for ghe in ghePhoThong if ghe.trangThai == False])

    # Tính giá vé
    gia_ve_thuong_gia = chuyenBay.tinh_gia_ve('ThuongGia', datetime.now().strftime("%d/%m/%Y %H:%M"))
    gia_ve_pho_thong = chuyenBay.tinh_gia_ve('PhoThong', datetime.now().strftime("%d/%m/%Y %H:%M"))

    # Thông tin khách hàng mặc định
    ten_khach_hang = current_user.hoVaTen
    so_dien_thoai = current_user.soDienThoai
    email = current_user.email

    if request.method == 'POST':

        so_luong_ve = int(request.form['so_luong_ve'])
        loai_ve = request.form.get('loai_ve')
        ten_khach_hang = request.form.get('ten_khach_hang') or ten_khach_hang
        so_dien_thoai = request.form.get('so_dien_thoai') or so_dien_thoai
        email = request.form.get('email') or email


        session['dat_ve'] = {
            'ma_chuyen_bay': ma_chuyen_bay,
            'so_luong_ve': so_luong_ve,
            'loai_ve': loai_ve,
            'ten_khach_hang': ten_khach_hang,
            'so_dien_thoai': so_dien_thoai,
            'email': email,
            'gia_ve_thuong_gia': gia_ve_thuong_gia,
            'gia_ve_pho_thong': gia_ve_pho_thong

        }


        if loai_ve == 'ThuongGia' and so_luong_ve > soGheThuongGiaConLai:
            flash('Thất bại: Không đủ ghế Thương Gia.', 'danger')
            return redirect(url_for('dat_ve', ma_chuyen_bay=ma_chuyen_bay))
        if loai_ve == 'PhoThong' and so_luong_ve > soGhePhoThongConLai:
            flash('Thất bại: Không đủ ghế Phổ Thông.', 'danger')
            return redirect(url_for('dat_ve', ma_chuyen_bay=ma_chuyen_bay))


        gia_ve = gia_ve_thuong_gia if loai_ve == 'ThuongGia' else gia_ve_pho_thong
        total_price = gia_ve * so_luong_ve


        return redirect(url_for('thanh_toan', ma_chuyen_bay=ma_chuyen_bay, total_price=total_price, loai_ve=loai_ve,
                                so_luong_ve=so_luong_ve))


    gio_di_formatted = chuyenBay.gioDi.strftime("%H:%M, %d/%m/%Y")
    gio_den_formatted = chuyenBay.gioDen.strftime("%H:%M, %d/%m/%Y")

    return render_template('datve.html', chuyenBay=chuyenBay,
                           gia_ve_thuong_gia=gia_ve_thuong_gia, gia_ve_pho_thong=gia_ve_pho_thong,
                           gio_di_formatted=gio_di_formatted, gio_den_formatted=gio_den_formatted,
                           ten_khach_hang=ten_khach_hang, so_dien_thoai=so_dien_thoai, email=email,
                           soGheThuongGiaConLai=soGheThuongGiaConLai,
                           soGhePhoThongConLai=soGhePhoThongConLai )

@app.route('/thanh_toan', methods=['GET', 'POST'])
def thanh_toan():
    ma_chuyen_bay = request.args.get('ma_chuyen_bay')
    total_price = float(request.args.get('total_price'))
    loai_ve = request.args.get('loai_ve')
    so_luong_ve = int(request.args.get('so_luong_ve'))

    if request.method == 'POST':
        flash("Thanh toán thành công!", 'success')

        dat_ve = session.get('dat_ve')

        if dat_ve:
            chuyenBay = ChuyenBay.query.get_or_404(dat_ve['ma_chuyen_bay'])
            loai_ve = dat_ve['loai_ve']
            so_luong_ve = dat_ve['so_luong_ve']
            ten_khach_hang = dat_ve['ten_khach_hang']
            so_dien_thoai = dat_ve['so_dien_thoai']
            email = dat_ve['email']
            gia_ve_thuong_gia = dat_ve['gia_ve_thuong_gia']
            gia_ve_pho_thong = dat_ve['gia_ve_pho_thong']
            cccd = current_user.cccd


            gia_ve = gia_ve_thuong_gia if loai_ve == 'ThuongGia' else gia_ve_pho_thong
            total_price = gia_ve * so_luong_ve


            ghe_trong = Ghe.query.filter_by(maChuyenbay=chuyenBay.maChuyenBay, hangGhe=loai_ve, trangThai=False).limit(so_luong_ve).all()

            for ghe_con_lai in ghe_trong:
                ghe_con_lai.trangThai = True
                db.session.commit()

                ve = Ve(
                    tinhTrangVe='Đã đặt',
                    maChuyenBay=chuyenBay.maChuyenBay,
                    maKhachHang=current_user.maKhachHang,
                    maGhe=ghe_con_lai.maGhe,
                    maHangVe=1 if loai_ve == 'ThuongGia' else 2,
                    maNhanVien=None,     tenKhachHang=ten_khach_hang, soDienThoai=so_dien_thoai,
                    email=email, giaVe=gia_ve,   cccd = cccd     )
                db.session.add(ve)
                db.session.commit()


                giao_dich = LichSuGiaoDich(
                    maChuyenBay=chuyenBay.maChuyenBay,
                    maKhachHang=current_user.maKhachHang,
                    loaiVe=loai_ve,   soLuongVe=so_luong_ve,    giaVe=gia_ve,
                    tinhTrangVe='Đã đặt',  thoiGianGiaoDich = datetime.now(),  maGhe = ghe_con_lai.maGhe  )
                db.session.add(giao_dich)
                db.session.commit()
            session.pop('dat_ve', None)
        return redirect(url_for('hien_thi_ve', ma_chuyen_bay=ma_chuyen_bay, total_price=total_price,
                                loai_ve=loai_ve, so_luong_ve=so_luong_ve))


    chuyenBay = ChuyenBay.query.get_or_404(ma_chuyen_bay)

    return render_template('thanhtoan.html', chuyenBay=chuyenBay,
                           total_price=total_price, loai_ve=loai_ve, so_luong_ve=so_luong_ve)


@app.route('/banve/tim-chuyen-bay', methods=['GET', 'POST'])
@login_required
def tim_chuyen_bay_ban_ve():
    if isinstance(current_user, NhanVien) and current_user.vaiTro == VaiTro.BANVE:
        sanBays = SanBay.query.all()
        chuyenBays = []

        if request.method == 'POST':
            sanBayDi = request.form['sanBayDi']
            sanBayDen = request.form['sanBayDen']
            ngayDi = request.form['ngayDi']

            current_time = datetime.now()

            min_time = current_time + timedelta(hours=4)

            chuyenBays = ChuyenBay.query.join(TuyenBay).filter(
                TuyenBay.maSanBayDi == sanBayDi,
                TuyenBay.maSanBayDen == sanBayDen,
                ChuyenBay.gioDi >= min_time

            ).order_by(ChuyenBay.gioDi).all()

        return render_template('banve_timchuyenbay.html', sanBays=sanBays, chuyenBays=chuyenBays)

    return redirect('/login')

@app.route('/banve/banve/<int:ma_chuyen_bay>', methods=['GET', 'POST'])
def ban_ve(ma_chuyen_bay):
    chuyenBay = ChuyenBay.query.get_or_404(ma_chuyen_bay)

    gia_ve_thuong_gia = chuyenBay.tinh_gia_ve('ThuongGia', datetime.now().strftime("%d/%m/%Y %H:%M"))
    gia_ve_pho_thong = chuyenBay.tinh_gia_ve('PhoThong', datetime.now().strftime("%d/%m/%Y %H:%M"))
    total_price = None

    gheThuongGia = Ghe.query.filter_by(maChuyenbay=chuyenBay.maChuyenBay, hangGhe='ThuongGia').all()
    ghePhoThong = Ghe.query.filter_by(maChuyenbay=chuyenBay.maChuyenBay, hangGhe='PhoThong').all()

    soGheThuongGiaConLai = len([ghe for ghe in gheThuongGia if ghe.trangThai == False])
    soGhePhoThongConLai = len([ghe for ghe in ghePhoThong if ghe.trangThai == False])

    if request.method == 'POST':
        so_luong_ve = int(request.form['so_luong_ve'])
        loai_ve = request.form.get('loai_ve')
        ten_nguoi_mua = request.form['ten_nguoi_mua']
        so_dien_thoai = request.form['so_dien_thoai']
        email = request.form['email']
        cccd = request.form['cccd']


        if loai_ve == 'ThuongGia' and so_luong_ve > soGheThuongGiaConLai:
            flash('Thất bại: Không đủ ghế Thương Gia.', 'danger')
            return redirect(url_for('ban_ve', ma_chuyen_bay=ma_chuyen_bay))

        if loai_ve == 'PhoThong' and so_luong_ve > soGhePhoThongConLai:
            flash('Thất bại: Không đủ ghế Phổ Thông.', 'danger')
            return redirect(url_for('ban_ve', ma_chuyen_bay=ma_chuyen_bay))

        if loai_ve == 'ThuongGia':
            gia_ve = gia_ve_thuong_gia
            maHangVe = 1
        elif loai_ve == 'PhoThong':
            gia_ve = gia_ve_pho_thong
            maHangVe = 2


        total_price = gia_ve * so_luong_ve
        ma_nhan_vien = current_user.maNhanVien


        ve_ids = []
        for _ in range(so_luong_ve):
            ghe_con_lai = Ghe.query.filter_by(maChuyenbay=chuyenBay.maChuyenBay, hangGhe=loai_ve, trangThai=False).first()


            if not ghe_con_lai:
                ghe_con_lai = Ghe(maMayBay=chuyenBay.maMayBay, hangGhe=loai_ve, trangThai=False, maChuyenbay=chuyenBay.maChuyenBay)
                db.session.add(ghe_con_lai)
                db.session.commit()

            ghe_con_lai.trangThai = True
            db.session.commit()

            ve = Ve(
                tinhTrangVe='Đã bán',  maChuyenBay=chuyenBay.maChuyenBay,   maKhachHang=None,
                maGhe=ghe_con_lai.maGhe,   maHangVe=maHangVe,  tenKhachHang=ten_nguoi_mua,
                email=email,  giaVe=gia_ve,    cccd=cccd,      maNhanVien=ma_nhan_vien , soDienThoai = so_dien_thoai    )
            db.session.add(ve)
            db.session.commit()
            ve_ids.append(ve.maVe)

        flash("Bán vé thành công!", 'success')
        return redirect(url_for('in_ve', ma_chuyen_bay=ma_chuyen_bay, ve_ids=ve_ids))

    # Định dạng giờ đi và giờ đến
    gio_di_formatted = chuyenBay.gioDi.strftime("%H:%M, %d/%m/%Y")
    gio_den_formatted = chuyenBay.gioDen.strftime("%H:%M, %d/%m/%Y")

    return render_template('banve_banve.html',
                           chuyenBay=chuyenBay,
                           gia_ve_thuong_gia=gia_ve_thuong_gia,
                           gia_ve_pho_thong=gia_ve_pho_thong,
                           total_price=total_price,
                           gio_di_formatted=gio_di_formatted,
                           gio_den_formatted=gio_den_formatted,
                           soGheThuongGiaConLai=soGheThuongGiaConLai,
                           soGhePhoThongConLai=soGhePhoThongConLai)

@app.route('/inve/<int:ma_chuyen_bay>', methods=['GET'])
def in_ve(ma_chuyen_bay):
    chuyenBay = ChuyenBay.query.get_or_404(ma_chuyen_bay)
    ve_ids = request.args.getlist('ve_ids')
    ves = Ve.query.filter(Ve.maVe.in_(ve_ids)).all()
    total_price = 0
    so_ghes = []
    gia_ve_list = []
    ghe_names = []

    for ve in ves:
        if ve.giaVe:
            total_price += ve.giaVe
            gia_ve_list.append(ve.giaVe)
        so_ghes.append(ve.maGhe)

        ghe = Ghe.query.get(ve.maGhe)
        if ghe:
            ghe_names.append(ghe.tenGhe)

    ves_and_names = list(zip(ves, ghe_names))
    return render_template('inve.html',
                           chuyenBay=chuyenBay,
                           ves_and_names=ves_and_names,  # Truyền kết quả zip
                           total_price=total_price,
                           so_ghes=so_ghes,
                           gia_ve_list=gia_ve_list)


@app.route('/thay-doi-thong-tin', methods=['GET', 'POST'])
@login_required
def change_info():
    form = ChangeInfoForm()
    if request.method == 'GET':
        if isinstance(current_user, KhachHang):
            form.ho_va_ten.data = current_user.hoVaTen
            form.email.data = current_user.email
            form.so_dien_thoai.data = current_user.soDienThoai
            form.tai_khoan.data = current_user.taiKhoan
            form.cccd.data = current_user.cccd

    if form.validate_on_submit():
        try:
            if isinstance(current_user, KhachHang):
                current_user.hoVaTen = form.ho_va_ten.data
                current_user.email = form.email.data
                current_user.soDienThoai = form.so_dien_thoai.data
                current_user.taiKhoan = form.tai_khoan.data
                current_user.cccd = form.cccd.data
            db.session.commit()
            app.logger.info(f"{current_user.hoVaTen}, {current_user.email}, {current_user.soDienThoai}, {current_user.taiKhoan}, {current_user.cccd}")

            flash('Thông tin đã được cập nhật', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

        return redirect(url_for('change_info'))

    return render_template('thaydoithongtin.html', form=form)



@app.route('/doi-mat-khau', methods=['GET', 'POST'])
@login_required
def doimatkhau():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.mat_khau_cu.data):  # Kiểm tra mật khẩu cũ
            current_user.matKhau = generate_password_hash(form.mat_khau_moi.data)  # Cập nhật mật khẩu mới
            db.session.commit()
            flash('Mật khẩu đã được thay đổi', 'success')
            return redirect(url_for('change_info'))
        else:
            flash('Mật khẩu cũ không đúng', 'danger')

    return render_template('doimatkhau.html', form=form)

@app.route('/tra-cuu-chuyen-bay')
@login_required
def tracuu_chuyen_bay():
    chuyen_bays = ChuyenBay.query.all()
    return render_template('tracuuchuyenbay.html', chuyen_bays=chuyen_bays)


@app.route('/xem-chuyen-bay/<int:maChuyenBay>')
@login_required
def xem_chuyen_bay(maChuyenBay):
    chuyen_bay = ChuyenBay.query.get_or_404(maChuyenBay)
    ve_list = Ve.query.filter_by(maChuyenBay=maChuyenBay).filter(Ve.tinhTrangVe != "Đã hủy").all()
    ghe_ve_info = []
    for ghe in chuyen_bay.ghe:

        ve = next((v for v in ve_list if v.maGhe == ghe.maGhe), None)

        if ve and ghe.trangThai == 1:  # Nếu vé tồn tại và ghế đã được đặt
            khach_hang = {
                'tenKhachHang': ve.tenKhachHang,
                'soDienThoai': ve.soDienThoai
            }
        else:
            khach_hang = None  # Ghế trống hoặc chưa có vé đặt

        ghe_ve_info.append({
            'tenGhe': ghe.tenGhe,
            'maGhe': ghe.maGhe,
            'hangGhe': ghe.hangGhe,
            've': ve,
            'khachHang': khach_hang
        })
    return render_template('xemchuyenbay.html', chuyen_bay=chuyen_bay, ghe_ve_info=ghe_ve_info)


@app.route('/hien_thi_ve', methods=['GET', 'POST'])
def hien_thi_ve():
    ma_chuyen_bay = request.args.get('ma_chuyen_bay')
    total_price = request.args.get('total_price')
    loai_ve = request.args.get('loai_ve')
    so_luong_ve = request.args.get('so_luong_ve')

    chuyenBay = ChuyenBay.query.get_or_404(ma_chuyen_bay)

    return render_template('vethanhtoan.html',
                           chuyenBay=chuyenBay,total_price=total_price,ma_chuyen_bay=ma_chuyen_bay,
                           loai_ve=loai_ve,so_luong_ve=so_luong_ve)


@app.route('/lich_su_giao_dich', methods=['GET'])
@login_required
def lich_su_giao_dich():
    now = datetime.utcnow()  # Lấy thời gian hiện tại
    if isinstance(current_user, KhachHang):
        giao_dichs = LichSuGiaoDich.query.filter_by(maKhachHang=current_user.maKhachHang).all()

        # Kiểm tra và cập nhật trạng thái vé nếu cần
        for giao_dich in giao_dichs:
            if giao_dich.tinhTrangVe == 'Đã đặt' and giao_dich.chuyenBay.gioDi and giao_dich.chuyenBay.gioDi < now:
                giao_dich.tinhTrangVe = 'Đã sử dụng'
                db.session.commit()

    else:
        flash("Bạn không có quyền truy cập lịch sử giao dịch!", "danger")
        return redirect(url_for('index'))

    # Nếu không có giao dịch nào
    if not giao_dichs:
        flash("Bạn chưa có giao dịch nào.", "info")
        return render_template('lichsugiaodich.html', giao_dichs=giao_dichs, now=now, timedelta=timedelta)

    # Trả về trang hiển thị lịch sử giao dịch với thông tin các vé
    return render_template('lichsugiaodich.html', giao_dichs=giao_dichs, now=now, timedelta=timedelta)

@app.route('/huy_ve/<int:giao_dich_id>', methods=['POST'])
@login_required
def huy_ve(giao_dich_id):
    if isinstance(current_user, KhachHang):
        giao_dich = LichSuGiaoDich.query.get(giao_dich_id)

        if not giao_dich or giao_dich.maKhachHang != current_user.maKhachHang:
            flash("Giao dịch không hợp lệ.", "danger")
            return redirect(url_for('lich_su_giao_dich'))


        if giao_dich.chuyenBay.gioDi and giao_dich.chuyenBay.gioDi > datetime.utcnow() + timedelta(hours=72):
            giao_dich.tinhTrangVe = 'Đã hủy'


            ghe = Ghe.query.filter_by(maChuyenbay=giao_dich.maChuyenBay, maGhe=giao_dich.maGhe).first()
            if ghe:
                ghe.trangThai = False
                db.session.commit()
                flash("Vé đã được hủy thành công!", "success")
                ve = Ve.query.filter_by(maChuyenBay=giao_dich.maChuyenBay, maGhe=giao_dich.maGhe).first()
                if ve:
                    # Cập nhật trạng thái vé thành "Đã hủy"
                    ve.tinhTrangVe = "Đã hủy"  # Cập nhật trạng thái vé trong bảng LichSuGiaoDich
                    db.session.commit()
            else:
                flash("Không tìm thấy ghế tương ứng với giao dịch.", "danger")
                db.session.rollback()

        else:
            flash("Bạn không thể hủy vé vì còn ít hơn 72 giờ trước giờ bay.", "danger")

        return redirect(url_for('lich_su_giao_dich'))
    else:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for('index'))


@app.route('/hoso')
@login_required
def account():
    user_info = get_user_info()
    return render_template('hoso.html', user_info=user_info)

@app.template_filter('currency_format')
def currency_format(value):
    if isinstance(value, str):
        value = float(value)
    return "{:,.0f}".format(value)



if __name__ == '__main__':
    from cbapp.admin import *
    app.run(debug=True)

