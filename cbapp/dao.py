from calendar import month

from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.sql.functions import count
from cbapp.models import NhanVien, KhachHang, SanBay, TuyenBay, ChuyenBay, Ve, LichSuGiaoDich, Ghe, HangVe, VaiTro, \
    MayBay
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


def get_so_luong_user():
    so_khach_hang = db.session.query(func.count(KhachHang.maKhachHang)).filter(KhachHang.active == True).scalar()
    so_nhan_vien = db.session.query(func.count(NhanVien.maNhanVien)).scalar()
    result = {
        'so_khach_hang': so_khach_hang,
        'so_nhan_vien': so_nhan_vien
    }
    return result


def get_so_luong_tong_quat():
    so_may_bay = db.session.query(func.count(MayBay.maMayBay)).scalar()
    so_tuyen_bay = db.session.query(func.count(TuyenBay.maTuyenBay)).scalar()
    so_chuyen_bay = db.session.query(func.count(ChuyenBay.maChuyenBay)).scalar()
    result = {
        'so_may_bay': so_may_bay,
        'so_tuyen_bay': so_tuyen_bay,
        'so_chuyen_bay': so_chuyen_bay
    }
    return result


def get_doanh_thu_tuyen_bay():
    return db.session.query(TuyenBay.maTuyenBay, TuyenBay.tenTuyenBay, func.sum(Ve.giaVe))\
            .join(ChuyenBay, TuyenBay.maTuyenBay.__eq__(ChuyenBay.maTuyenBay)).join(Ve, ChuyenBay.maChuyenBay.__eq__(Ve.maChuyenBay)) \
            .filter(Ve.tinhTrangVe != "Đã hủy") \
            .group_by(TuyenBay.maTuyenBay, TuyenBay.tenTuyenBay).all()


def get_doanh_thu_tuyen_bay_theo_thang(month=datetime.now().month, year=datetime.now().year):
    return db.session.query(TuyenBay.maTuyenBay, TuyenBay.tenTuyenBay, func.sum(Ve.giaVe))\
            .join(ChuyenBay, TuyenBay.maTuyenBay == ChuyenBay.maTuyenBay)\
            .join(Ve, ChuyenBay.maChuyenBay == Ve.maChuyenBay)\
            .filter(Ve.tinhTrangVe != "Đã hủy")\
            .filter(func.extract('month', Ve.ngayTaoVe) == month)\
            .filter(func.extract('year', Ve.ngayTaoVe) == year)\
            .group_by(TuyenBay.maTuyenBay, TuyenBay.tenTuyenBay).all()


def get_so_chuyen_bay_cua_tuyen_bay():
    return db.session.query(TuyenBay.maTuyenBay, func.count(ChuyenBay.maTuyenBay)).outerjoin(ChuyenBay, TuyenBay.maTuyenBay.__eq__(ChuyenBay.maTuyenBay))\
            .group_by(TuyenBay.maTuyenBay).all()


def get_so_chuyen_bay_cua_tuyen_bay_theo_thang(month=datetime.now().month, year=datetime.now().year):
    return db.session.query(TuyenBay.maTuyenBay, func.count(ChuyenBay.maTuyenBay)).outerjoin(ChuyenBay, TuyenBay.maTuyenBay.__eq__(ChuyenBay.maTuyenBay))\
            .group_by(TuyenBay.maTuyenBay).filter(func.extract('month', ChuyenBay.gioDi).__eq__(month) and func.extract('year', ChuyenBay.gioDi).__eq__(year)).all()


def get_so_ve_nhan_vien_ban():
    return db.session.query(NhanVien.maNhanVien, NhanVien.tenNhanVien, func.count(Ve.maNhanVien), func.sum(Ve.giaVe))\
            .join(Ve, NhanVien.maNhanVien == Ve.maNhanVien)\
            .filter(Ve.tinhTrangVe != "Đã hủy")\
            .group_by(NhanVien.maNhanVien)\
            .filter(NhanVien.vaiTro == VaiTro.BANVE).all()

def get_so_ve_nhan_vien_ban_theo_thang(month=datetime.now().month, year=datetime.now().year):
    return db.session.query(NhanVien.maNhanVien, NhanVien.tenNhanVien, func.count(Ve.maNhanVien), func.sum(Ve.giaVe))\
            .join(Ve, NhanVien.maNhanVien == Ve.maNhanVien)\
            .filter(Ve.tinhTrangVe != "Đã hủy")\
            .filter(func.extract('month', Ve.ngayTaoVe) == month)\
            .filter(func.extract('year', Ve.ngayTaoVe) == year)\
            .group_by(NhanVien.maNhanVien).all()

def get_doanh_thu():
    return db.session.query(func.sum(Ve.giaVe))\
            .filter(Ve.tinhTrangVe != "Đã hủy")\
            .all()
def get_doanh_thu_theo_nam(year=datetime.now().year):
    return db.session.query(func.extract('month', Ve.ngayTaoVe), func.sum(Ve.giaVe))\
            .filter(Ve.tinhTrangVe != "Đã hủy")\
            .group_by(func.extract('month', Ve.ngayTaoVe))\
            .filter(func.extract('year', Ve.ngayTaoVe) == year)\
            .order_by(func.extract('month', Ve.ngayTaoVe)).all()

def get_user_info():
    user_info = {
        'username': current_user.taiKhoan,
        'email': current_user.email,
        'hoVaTen': current_user.hoVaTen,
        'soDienThoai': current_user.soDienThoai,
        'cccd': current_user.cccd
    }
    return user_info
if __name__ == '__main__':
    with app.app_context():
        print(get_doanh_thu_theo_nam())