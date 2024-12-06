
# models.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, Date, DateTime
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

from cbapp import app, db, create_db


class KhachHang(db.Model, UserMixin):
    __tablename__ = 'khachhang'
    maKhachHang = Column(Integer, primary_key=True, autoincrement=True)
    hoVaTen = Column(String(50), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    soDienThoai = Column(String(12), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    taiKhoan = Column(String(30), unique=True, nullable=False)
    matKhau = Column(String(255), nullable=False)

    def set_password(self, password):
        self.matKhau = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.matKhau, password)

    def get_id(self):
        return str(self.maKhachHang)


class NhanVien(db.Model, UserMixin):
    __tablename__ = 'nhanvien'
    maNhanVien = Column(Integer, primary_key=True, autoincrement=True)
    tenNhanVien = Column(String(50), nullable=False)
    soDienThoai = Column(String(12), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    vaiTro = Column(String(50), nullable=False)
    taiKhoan = Column(String(30), unique=True, nullable=False)
    matKhau = Column(String(255), nullable=False)

    def set_password(self, password):
        self.matKhau = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.matKhau, password)

    def get_id(self):
        return str(self.maNhanVien)


class SanBay(db.Model):
    __tablename__ = 'sanbay'
    maSanBay = db.Column(db.String(10), primary_key=True)
    tenSanBay = db.Column(db.String(100), nullable=False)


class TuyenBay(db.Model):
    __tablename__ = 'tuyenbay'
    maTuyenBay = db.Column(Integer, primary_key=True, autoincrement=True)
    tenTuyenBay = db.Column(db.String(50), nullable=False)
    maSanBayDi = db.Column(db.String(10), db.ForeignKey('sanbay.maSanBay'), nullable=False)
    maSanBayDen = db.Column(db.String(10), db.ForeignKey('sanbay.maSanBay'), nullable=False)

    sanBayTrungGian = db.Column(db.JSON, nullable=True)

    sanBayDi = db.relationship('SanBay', foreign_keys=[maSanBayDi], backref='sanbay_di', lazy='select')
    sanBayDen = db.relationship('SanBay', foreign_keys=[maSanBayDen], backref='sanbay_den', lazy='select')


class MayBay(db.Model):
    __tablename__ = 'maybay'
    maMayBay = Column(Integer, primary_key=True, autoincrement=True)
    loaiMayBay = Column(String(50), nullable=False)
    tongSoGhe = Column(Integer, nullable=False)
    GheHang1 = Column(Integer, nullable=False)
    GheHang2 = Column(Integer, nullable=False)

    chuyenBays = relationship('ChuyenBay', backref='mayBay', cascade="all, delete-orphan")
    ghes = relationship('Ghe', backref='mayBay', cascade="all, delete-orphan")


class ChuyenBay(db.Model):
    __tablename__ = 'chuyenbay'
    maChuyenBay = Column(Integer, primary_key=True, autoincrement=True)
    gioDi = Column(DateTime, nullable=False)
    gioDen = Column(DateTime, nullable=False)
    ngayBay = Column(Date, nullable=False, default=date.today)
    ngayDen = Column(Date, nullable=False)

    maTuyenBay = Column(Integer, ForeignKey('tuyenbay.maTuyenBay'), nullable=False)
    maMayBay = Column(Integer, ForeignKey('maybay.maMayBay'), nullable=False)

    ves = relationship('Ve', backref='chuyenBay', cascade="all, delete-orphan")


class Ghe(db.Model):
    __tablename__ = 'ghe'
    maGhe = Column(Integer, primary_key=True, autoincrement=True)
    tenGhe = Column(String(50), nullable=False)
    trangThai = Column(Boolean, nullable=False)
    hangGhe = Column(String(50), nullable=False)
    maMayBay = Column(Integer, ForeignKey('maybay.maMayBay'), nullable=False)

    ves = relationship('Ve', backref='ghe', cascade="all, delete-orphan")


class HangVe(db.Model):
    __tablename__ = 'hangve'
    maHangVe = Column(Integer, primary_key=True, autoincrement=True)
    tenHangVe = Column(String(50), nullable=False)

    ves = relationship('Ve', backref='hangVe', cascade="all, delete-orphan")


class GiaVe(db.Model):
    __tablename__ = 'giave'
    maGiaVe = Column(Integer, primary_key=True, autoincrement=True)
    tenGiaVe = Column(String(50), nullable=False)

    ves = relationship('Ve', backref='giaVe', cascade="all, delete-orphan")


class Ve(db.Model):
    __tablename__ = 've'
    maVe = Column(Integer, primary_key=True, autoincrement=True)
    tinhTrangVe = Column(String(50), nullable=False)
    maChuyenBay = Column(Integer, ForeignKey('chuyenbay.maChuyenBay'), nullable=False)
    maKhachHang = Column(Integer, ForeignKey('khachhang.maKhachHang'), nullable=False)
    maGhe = Column(Integer, ForeignKey('ghe.maGhe'), nullable=False)
    maHangVe = Column(Integer, ForeignKey('hangve.maHangVe'), nullable=False)
    maGiaVe = Column(Integer, ForeignKey('giave.maGiaVe'), nullable=True)
    maNhanVien = Column(Integer, ForeignKey('nhanvien.maNhanVien'), nullable=True)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        haNoi = SanBay(maSanBay="HAN", tenSanBay="Sân bay Nội Bài, Hà Nội")
        saiGon = SanBay(maSanBay="SGN", tenSanBay="Sân bay Tân Sơn Nhất, Sài Gòn")
        daNang = SanBay(maSanBay="DAD", tenSanBay="Sân bay Quốc tế Đà Nẵng")

        db.session.add_all([haNoi, saiGon, daNang])
        db.session.commit()

