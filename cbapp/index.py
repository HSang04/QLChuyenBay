from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from cbapp import app, dao, login, db, create_db
from cbapp.models import KhachHang, NhanVien, Ghe, Ve


@app.route('/')
def index():
    return redirect('/trangchu')



@app.route('/login', methods=['GET', 'POST'])
def login_process():
    err_msg = None
    if request.method == 'POST':
        tai_khoan = request.form['taiKhoan']
        mat_khau = request.form['matKhau']

        # Kiểm tra thông tin đăng nhập
        user = dao.auth_user(taiKhoan=tai_khoan, matKhau=mat_khau)

        if user:
            login_user(user)  # Flask-Login sẽ lưu ID người dùng vào session


            if isinstance(user, NhanVien):
                if user.vaiTro == VaiTro.BANVE:
                    return redirect('/banve')
                elif user.vaiTro == VaiTro.QUANTRI:
                    return redirect('/admin')
            elif isinstance(user, KhachHang):
                return redirect('/trangchu')
        else:
            err_msg = "Sai tài khoản hoặc mật khẩu."

    return render_template('login.html', err_msg=err_msg)

@app.route('/logout')
def logout():
    logout_user()  # Xóa ID người dùng khỏi session
    flash('Bạn đã đăng xuất thành công!', 'success')
    return redirect('/login')



@login.user_loader
def load_user(user_id):

    user = dao.get_nhan_vien_by_id(user_id)
    if user:
        return user


    user = KhachHang.query.get(user_id)
    if user:
        return user

    return None


#
@app.route('/banve')
def banve():
    if isinstance(current_user, NhanVien) and current_user.vaiTro.__eq__(VaiTro.BANVE):
        return render_template('banve.html')
    return redirect('/login')


# @app.route('/quantri')
# def quantri():
#     if isinstance(current_user, NhanVien) and current_user.vaiTro.__eq__(VaiTro.QUANTRI):
#         return render_template('quantri.html')
#     return redirect('/login')


@app.route('/trangchu')
def trangchu():
    # Kiểm tra xem người dùng đã đăng nhập chưa
    if not current_user.is_authenticated:
        return redirect('/login')  # Nếu chưa đăng nhập, chuyển hướng đến trang đăng nhập

    # Nếu người dùng là nhân viên bán vé, chuyển hướng đến trang bán vé
    if isinstance(current_user, NhanVien) and current_user.vaiTro == VaiTro.BANVE:
        return redirect('/banve')

    # Nếu người dùng là nhân viên quản trị, chuyển hướng đến trang quản trị
    elif isinstance(current_user, NhanVien) and current_user.vaiTro == VaiTro.QUANTRI:
        return redirect('/admin')

    # Nếu người dùng là khách hàng, tiếp tục ở trang chủ
    elif isinstance(current_user, KhachHang):
        sanBays = SanBay.query.all()

        # Handle form submission
        sanBayDi = request.args.get('sanBayDi')
        sanBayDen = request.args.get('sanBayDen')
        ngayDi = request.args.get('ngayDi')

        # Sửa lại query để lọc qua bảng TuyenBay thay vì trực tiếp qua ChuyenBay
        chuyenBays = ChuyenBay.query.join(TuyenBay).filter(
            (TuyenBay.maSanBayDi == sanBayDi if sanBayDi else True) &
            (TuyenBay.maSanBayDen == sanBayDen if sanBayDen else True) &
            (ChuyenBay.gioDi >= datetime.strptime(ngayDi, '%Y-%m-%d') if ngayDi else True)
        ).all()

        return render_template('trangchu.html', sanBays=sanBays, chuyenBays=chuyenBays)

    # Nếu không phải nhân viên bán vé hay khách hàng, điều hướng đến trang login
    return redirect('/login')

@app.route('/tim-chuyen-bay', methods=['GET', 'POST'])
def tim_chuyen_bay():
    if current_user.is_authenticated and isinstance(current_user, NhanVien) and current_user.vaiTro == VaiTro.BANVE:
        # Nếu là nhân viên bán vé, chuyển hướng đến trang tìm chuyến bay của nhân viên bán vé
        return redirect('/banve/tim-chuyen-bay')

    sanBays = SanBay.query.all()  # Lấy danh sách tất cả sân bay
    chuyenBays = []  # Khởi tạo danh sách chuyến bay

    if request.method == 'POST':
        sanBayDi = request.form['sanBayDi']
        sanBayDen = request.form['sanBayDen']
        ngayDi = request.form['ngayDi']

        # Lọc chuyến bay theo thông tin từ form
        chuyenBays = ChuyenBay.query.join(TuyenBay).filter(
            TuyenBay.maSanBayDi == sanBayDi,
            TuyenBay.maSanBayDen == sanBayDen,
            ChuyenBay.gioDi >= datetime.strptime(ngayDi, '%Y-%m-%d')
        ).all()

    return render_template('timchuyenbay.html', sanBays=sanBays, chuyenBays=chuyenBays)
@app.route('/dat_ve/<int:ma_chuyen_bay>', methods=['GET', 'POST'])
def dat_ve(ma_chuyen_bay):
    if not current_user.is_authenticated:
        return render_template('login.html')

    chuyenBay = ChuyenBay.query.get_or_404(ma_chuyen_bay)
    total_price = None  # Biến tổng giá vé
    so_luong_ve = 0
    loai_ve = ''

    # Tính giá vé cho từng loại vé
    gia_ve_thuong_gia = chuyenBay.tinh_gia_ve('ThuongGia', datetime.now().strftime("%d/%m/%Y %H:%M"))
    gia_ve_pho_thong = chuyenBay.tinh_gia_ve('PhoThong', datetime.now().strftime("%d/%m/%Y %H:%M"))

    if request.method == 'POST':
        so_luong_ve = int(request.form['so_luong_ve'])
        loai_ve = request.form.get('loai_ve')

        # Xác định giá vé dựa trên loại vé đã chọn
        if loai_ve == 'ThuongGia':
            gia_ve = gia_ve_thuong_gia
        elif loai_ve == 'PhoThong':
            gia_ve = gia_ve_pho_thong

        # Tính tổng giá vé
        total_price = gia_ve * so_luong_ve

        # Chuyển hướng tới trang ThanhToan và truyền các tham số
        return redirect(url_for('thanh_toan', ma_chuyen_bay=ma_chuyen_bay, total_price=total_price,
                                loai_ve=loai_ve, so_luong_ve=so_luong_ve))

    # Format giờ bay để hiển thị
    gio_di_formatted = chuyenBay.gioDi.strftime("%H:%M, %d/%m/%Y")
    gio_den_formatted = chuyenBay.gioDen.strftime("%H:%M, %d/%m/%Y")

    return render_template('datve.html', chuyenBay=chuyenBay,
                           gia_ve_thuong_gia=gia_ve_thuong_gia, gia_ve_pho_thong=gia_ve_pho_thong,
                           gio_di_formatted=gio_di_formatted, gio_den_formatted=gio_den_formatted,
                           total_price=total_price)

@app.route('/thanh_toan', methods=['GET', 'POST'])
def thanh_toan():
    # Lấy các tham số từ query string
    ma_chuyen_bay = request.args.get('ma_chuyen_bay')
    total_price = request.args.get('total_price')
    loai_ve = request.args.get('loai_ve')
    so_luong_ve = request.args.get('so_luong_ve')

    if request.method == 'POST':
        # Thực hiện thanh toán (có thể thêm logic thanh toán ở đây)
        flash("Thanh toán thành công!", 'success')
        return redirect('/trangchu')

    # Lấy thông tin chuyến bay từ cơ sở dữ liệu
    chuyenBay = ChuyenBay.query.get_or_404(ma_chuyen_bay)

    return render_template('thanhtoan.html', chuyenBay=chuyenBay,
                           total_price=total_price, loai_ve=loai_ve, so_luong_ve=so_luong_ve)


@app.route('/banve/tim-chuyen-bay', methods=['GET', 'POST'])
@login_required
def tim_chuyen_bay_ban_ve():
    # Kiểm tra nếu người dùng là nhân viên bán vé
    if isinstance(current_user, NhanVien) and current_user.vaiTro == VaiTro.BANVE:
        sanBays = SanBay.query.all()  # Lấy danh sách tất cả sân bay
        chuyenBays = []  # Khởi tạo danh sách chuyến bay

        if request.method == 'POST':
            sanBayDi = request.form['sanBayDi']
            sanBayDen = request.form['sanBayDen']
            ngayDi = request.form['ngayDi']

            # Sửa lại query để lọc qua bảng TuyenBay thay vì trực tiếp qua ChuyenBay
            chuyenBays = ChuyenBay.query.join(TuyenBay).filter(
                TuyenBay.maSanBayDi == sanBayDi,
                TuyenBay.maSanBayDen == sanBayDen,
                ChuyenBay.gioDi >= datetime.strptime(ngayDi, '%Y-%m-%d')
            ).all()

        return render_template('banve_timchuyenbay.html', sanBays=sanBays, chuyenBays=chuyenBays)

    return redirect('/login')

@app.route('/banve/banve/<int:ma_chuyen_bay>', methods=['GET', 'POST'])
def ban_ve(ma_chuyen_bay):
    chuyenBay = ChuyenBay.query.get_or_404(ma_chuyen_bay)

    # Tính giá vé cho các loại vé
    gia_ve_thuong_gia = chuyenBay.tinh_gia_ve('ThuongGia', datetime.now().strftime("%d/%m/%Y %H:%M"))
    gia_ve_pho_thong = chuyenBay.tinh_gia_ve('PhoThong', datetime.now().strftime("%d/%m/%Y %H:%M"))
    total_price = None

    # Kiểm tra số ghế còn lại trên chuyến bay
    gheThuongGia = Ghe.query.filter_by(maMayBay=chuyenBay.maMayBay, hangGhe='ThuongGia').all()
    ghePhoThong = Ghe.query.filter_by(maMayBay=chuyenBay.maMayBay, hangGhe='PhoThong').all()

    soGheThuongGiaConLai = len([ghe for ghe in gheThuongGia if ghe.trangThai == False])
    soGhePhoThongConLai = len([ghe for ghe in ghePhoThong if ghe.trangThai == False])

    if request.method == 'POST':
        so_luong_ve = int(request.form['so_luong_ve'])
        loai_ve = request.form.get('loai_ve')
        ten_nguoi_mua = request.form['ten_nguoi_mua']
        so_dien_thoai = request.form['so_dien_thoai']
        email = request.form['email']

        # Kiểm tra xem có đủ ghế không
        if loai_ve == 'ThuongGia' and so_luong_ve > soGheThuongGiaConLai:
            flash('Thất bại: Không đủ ghế Thương Gia.', 'danger')
            return redirect(url_for('ban_ve', ma_chuyen_bay=ma_chuyen_bay))

        if loai_ve == 'PhoThong' and so_luong_ve > soGhePhoThongConLai:
            flash('Thất bại: Không đủ ghế Phổ Thông.', 'danger')
            return redirect(url_for('ban_ve', ma_chuyen_bay=ma_chuyen_bay))

        # Xác định giá vé và mã hạng vé
        if loai_ve == 'ThuongGia':
            gia_ve = gia_ve_thuong_gia
            maHangVe = 1  # Mã tương ứng với Thương Gia
        elif loai_ve == 'PhoThong':
            gia_ve = gia_ve_pho_thong
            maHangVe = 2  # Mã tương ứng với Phổ Thông

        # Tính tổng giá vé
        total_price = gia_ve * so_luong_ve

        # Tạo vé và lưu thông tin vào cơ sở dữ liệu
        ve_ids = []
        for _ in range(so_luong_ve):
            ghe_con_lai = Ghe.query.filter_by(maMayBay=chuyenBay.maMayBay, hangGhe=loai_ve, trangThai=False).first()
            if ghe_con_lai:
                # Đánh dấu ghế đã bán
                ghe_con_lai.trangThai = True
                db.session.commit()

                # Tạo vé mới và gán giá vé vào
                ve = Ve(
                    tinhTrangVe='Đã bán',
                    maChuyenBay=chuyenBay.maChuyenBay,
                    maKhachHang=None,  # Nếu là bán vé, không cần maKhachHang
                    maGhe=ghe_con_lai.maGhe,
                    maHangVe=maHangVe,  # Sử dụng maHangVe xác định đúng loại ghế
                    tenKhachHang=ten_nguoi_mua,  # Thông tin khách hàng bán vé
                    soDienThoai=so_dien_thoai,
                    email=email,
                    giaVe=gia_ve  # Lưu giá vé vào trường giaVe của vé
                )
                db.session.add(ve)
                db.session.commit()

                # Lưu ID của vé đã bán
                ve_ids.append(ve.maVe)

        flash("Bán vé thành công!", 'success')

        # Chuyển hướng đến trang in vé, kèm theo các ID vé đã bán
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
    # Lấy thông tin chuyến bay
    chuyenBay = ChuyenBay.query.get_or_404(ma_chuyen_bay)

    # Lấy các vé đã bán theo ID
    ve_ids = request.args.getlist('ve_ids')
    ves = Ve.query.filter(Ve.maVe.in_(ve_ids)).all()

    # Tính tổng tiền và lấy các số ghế đã chọn
    total_price = 0
    so_ghes = []
    gia_ve_list = []  # Danh sách giá vé

    for ve in ves:
        # Lấy giá vé trực tiếp từ trường giaVe của vé
        if ve.giaVe:  # Kiểm tra xem giaVe có giá trị không
            total_price += ve.giaVe  # Thêm giá vé vào tổng tiền
            gia_ve_list.append(ve.giaVe)  # Lưu giá vé vào danh sách giá vé
        so_ghes.append(ve.maGhe)  # Lưu số ghế đã chọn

    # Truyền dữ liệu vào template
    return render_template('inve.html',
                           chuyenBay=chuyenBay,
                           ves=ves,
                           total_price=total_price,
                           so_ghes=so_ghes,
                           gia_ve_list=gia_ve_list)


if __name__ == '__main__':
    from cbapp.admin import *
    app.run(debug=True)
