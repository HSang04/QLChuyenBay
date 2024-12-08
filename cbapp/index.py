from flask import Flask, render_template, request, redirect, flash, url_for, session
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from cbapp import app, dao, login, db, create_db
from cbapp.models import KhachHang, NhanVien


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
                if user.vaiTro == 'BANVE':
                    return redirect('/banve')
                elif user.vaiTro == 'QUANTRI':
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
    if isinstance(current_user, NhanVien) and current_user.vaiTro == 'BANVE':
        return render_template('banve.html')
    return redirect('/login')



@app.route('/quantri')
def quantri():
    if isinstance(current_user, NhanVien) and current_user.vaiTro == 'QUANTRI':
        return render_template('quantri.html')
    return redirect('/login')


@app.route('/trangchu')
def trangchu():

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

@app.route('/tim-chuyen-bay', methods=['GET', 'POST'])
def tim_chuyen_bay():
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


if __name__ == '__main__':
    from cbapp.admin import *
    app.run(debug=True)
