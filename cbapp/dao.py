from sqlalchemy import func
from sqlalchemy.sql.functions import count
from cbapp.models import NhanVien, KhachHang, SanBay, TuyenBay, ChuyenBay, Ve, LichSuGiaoDich, Ghe, HangVe
from cbapp import db, app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


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

def doanh_thu_tuyen_bay():
    return (db.session.query(TuyenBay.maTuyenBay, TuyenBay.tenTuyenBay, count(Ve.maVe) * Ve.giaVe).
            outerjoin(ChuyenBay, ChuyenBay.maTuyenBay.__eq__(TuyenBay.maTuyenBay)).outerjoin(Ve, Ve.maChuyenBay.__eq__(ChuyenBay.maChuyenBay)).
            group_by(TuyenBay.maTuyenBay, Ve.maChuyenBay, Ve.giaVe).all())


def doanh_thu_tuyen_bay_theo_thoi_gian(time='month', year=datetime.utcnow()):
    return db.session.query(TuyenBay.maTuyenBay, TuyenBay.tenTuyenBay, func.extract(time, Ve.ngayTaoVe), count(Ve.maVe) * Ve.giaVe)\
            .join(ChuyenBay, ChuyenBay.maTuyenBay.__eq__(TuyenBay.maTuyenBay)).join(Ve, Ve.maChuyenBay.__eq__(ChuyenBay.maChuyenBay))\
            .group_by(TuyenBay.maTuyenBay, func.extract(time, Ve.ngayTaoVe), Ve.maChuyenBay, Ve.giaVe)\
            .filter(func.extract('year', Ve.ngayTaoVe).__eq__(year)).all()


if __name__ == '__main__':
    with app.app_context():
        print(doanh_thu_tuyen_bay_theo_thoi_gian())