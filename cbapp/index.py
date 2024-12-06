from flask import Flask, render_template, request, redirect, flash
from flask_login import LoginManager, login_user, logout_user, current_user
from cbapp import app, dao, login, db, create_db
from cbapp.models import KhachHang, NhanVien

# Route gốc sẽ chuyển hướng đến trang login
@app.route('/')
def index():
    return redirect('/login')


# Route login để xử lý đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login_process():
    err_msg = None
    if request.method == 'POST':
        tai_khoan = request.form['taiKhoan']  # Lấy Tài Khoản từ form
        mat_khau = request.form['matKhau']  # Lấy Mật Khẩu từ form

        # Kiểm tra thông tin đăng nhập
        user = dao.auth_user(taiKhoan=tai_khoan, matKhau=mat_khau)

        if user:
            login_user(user)

            if isinstance(user, NhanVien):
                if user.vaiTro == 'BANVE':  # Đổi từ 'banve' thành 'BANVE'
                    return redirect('/banve')
                elif user.vaiTro == 'QUANTRI':  # Đổi từ 'quantri' thành 'QUANTRI'
                    return redirect('/admin')
            elif isinstance(user, KhachHang):
                return redirect('/khachhang')
        else:
            err_msg = "Sai tài khoản hoặc mật khẩu."

    return render_template('login.html', err_msg=err_msg)


# Route logout để đăng xuất
@app.route('/logout')
def logout():
    logout_user()
    return redirect('/login')


# Hàm load_user được gọi bởi Flask-Login để lấy user từ DB
@login.user_loader
def load_user(user_id):
    # Kiểm tra xem user_id có phải là của Nhân viên hay không
    user = dao.get_nhan_vien_by_id(user_id)
    if user:
        return user

    # Kiểm tra xem user_id có phải là của Khách hàng hay không
    user = KhachHang.query.get(user_id)
    if user:
        return user

    return None


# Route banve chỉ dành cho nhân viên bán vé
@app.route('/banve')
def banve():
    # Chỉ Admin Bán Vé mới có thể truy cập trang này
    if isinstance(current_user, NhanVien) and current_user.vaiTro == 'BANVE':  # Đổi từ 'banve' thành 'BANVE'
        return render_template('banve.html')
    return redirect('/login')


# Route quantri chỉ dành cho admin quản trị
@app.route('/quantri')
def quantri():
    # Chỉ Admin Quản Trị mới có thể truy cập trang này
    if isinstance(current_user, NhanVien) and current_user.vaiTro == 'QUANTRI':  # Đổi từ 'quantri' thành 'QUANTRI'
        return render_template('quantri.html')
    return redirect('/login')


# Route khachhang chỉ dành cho khách hàng
@app.route('/khachhang')
def khachhang():
    # Chỉ Khách hàng mới có thể truy cập trang này
    if isinstance(current_user, KhachHang):
        return render_template('khachhang.html')
    return redirect('/login')


if __name__ == '__main__':
    from cbapp.admin import *
    app.run(debug=True)
