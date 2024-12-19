from cbapp.models import NhanVien, KhachHang
from cbapp import db
from werkzeug.security import generate_password_hash, check_password_hash


def auth_user(taiKhoan, matKhau, role=None):
    # Kiểm tra Nhân Viên
    user = NhanVien.query.filter_by(taiKhoan=taiKhoan).first()
    if user and user.check_password(matKhau) and user.vaiTro.__eq__(role):
        return user

    # Kiểm tra Khách Hàng
    user = KhachHang.query.filter_by(taiKhoan=taiKhoan).first()
    if user and user.check_password(matKhau):
        return user

    return None


def get_nhan_vien_by_id(user_id):
    return NhanVien.query.get(user_id)


def get_khach_hang_by_id(user_id):
    return KhachHang.query.get(user_id)
