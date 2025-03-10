from datetime import datetime, timedelta
import logging
# admin.py
from flask import app, flash, redirect, request, jsonify
from flask_admin import Admin, expose, BaseView, AdminIndexView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form import Select2Widget, DateTimePickerWidget, DateTimeField
from flask_login import current_user, logout_user, login_required
from werkzeug.security import generate_password_hash
from wtforms import Form, StringField, SelectField, form
from wtforms.fields.choices import SelectMultipleField
from wtforms.fields.numeric import IntegerField
from wtforms.validators import DataRequired
from cbapp import app, db
from cbapp.dao import get_doanh_thu_tuyen_bay_theo_thang, get_so_luong_user, \
    get_so_ve_nhan_vien_ban_theo_thang, get_doanh_thu_theo_nam, get_so_chuyen_bay_cua_tuyen_bay_theo_thang, \
    get_so_luong_tong_quat
from cbapp.models import NhanVien, KhachHang, ChuyenBay, TuyenBay, SanBay, MayBay, VaiTro, Ghe, Ve, HangVe
from wtforms.validators import ValidationError
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectField


class QLCBAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        return self.render('admin/index.html', so_luong_user=get_so_luong_user(), so_luong_tong_quat=get_so_luong_tong_quat())



admin = Admin(app=app, name='Quản trị chuyến bay', template_mode='bootstrap4', index_view=QLCBAdminIndexView())


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.vaiTro.__eq__(VaiTro.QUANTRI)


class NhanVienAdmin(AdminView):
    column_list = ['tenNhanVien', 'email', 'soDienThoai','vaiTro']
    column_labels = dict(tenNhanVien='Tên Nhân Viên', soDienThoai='Số Điện Thoại', vaiTro='Vai Trò', taiKhoan='Tài khoản', matKhau='Mật khấu')
    column_searchable_list = ['tenNhanVien']
    form_choices = {
        'vaiTro': [(v.name, v.value) for v in VaiTro]}

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.active = True

            if 'matKhau' in form and form.matKhau.data:
                model.matKhau = generate_password_hash(form.matKhau.data)
        super(NhanVienAdmin, self).on_model_change(form, model, is_created)


class KhachHangAdmin(AdminView):
    column_list = ['hoVaTen', 'email', 'soDienThoai','active']
    column_labels = dict(hoVaTen='Họ và Tên', soDienThoai='Số Điện Thoại', taiKhoan ='Tài khoản', matKhau='Mật khẩu', cccd='Số căn cước công dân')
    column_searchable_list = ['hoVaTen']
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.active = True

            if 'matKhau' in form and form.matKhau.data:
                model.matKhau = generate_password_hash(form.matKhau.data)
        super(KhachHangAdmin, self).on_model_change(form, model, is_created)


class TuyenBayAdmin(AdminView):
    form_columns = ['tenTuyenBay', 'sanBayDi', 'sanBayDen', 'giaCoBan', 'sanBayTrungGian1', 'thoiGianDung1', 'sanBayTrungGian2', 'thoiGianDung2']
    column_list = ['maTuyenBay', 'tenTuyenBay', 'maSanBayDi', 'maSanBayDen']
    column_labels = dict(maTuyenBay='Mã Tuyến Bay', tenTuyenBay='Tên Tuyến Bay', sanBayDi='Sân Bay Đi', sanBayDen='Sân Bay Đến',
                         giaCoBan ='Giá phổ thông', sanBayTrungGian1 = 'Sân bay trung gian 1', thoigianDung1='Thời gian dừng'
                         , sanBayTrungGian2 = 'Sân bay trung gian 2', thoigianDung2='Thời gian dừng', maSanBayDi ='Mã sân bay đi'
                         ,maSanBayDen ='Mã sân bay đến')
    can_export = True
    column_searchable_list = ['tenTuyenBay']
    column_filters = ['maTuyenBay', 'tenTuyenBay']
    page_size = 10

    form_overrides = {
        'sanBayDi': QuerySelectField,
        'sanBayDen': QuerySelectField,
        'sanBayTrungGian1': QuerySelectField,
        'sanBayTrungGian2': QuerySelectField,
        'thoiGianDung1': SelectField,
        'thoiGianDung2': SelectField,
    }

    form_args = {
        'sanBayDi': {
            'query_factory': lambda: SanBay.query.all(),
            'get_label': lambda x: x.tenSanBay,
            'get_pk': lambda x: x.maSanBay
        },
        'sanBayDen': {
            'query_factory': lambda: SanBay.query.all(),
            'get_label': lambda x: x.tenSanBay,
            'get_pk': lambda x: x.maSanBay
        },
        'sanBayTrungGian1': {
            'query_factory': lambda: SanBay.query.all(),
            'get_label': lambda x: x.tenSanBay,
            'get_pk': lambda x: x.maSanBay
        },
        'sanBayTrungGian2': {
            'query_factory': lambda: SanBay.query.all(),
            'get_label': lambda x: x.tenSanBay,
            'get_pk': lambda x: x.maSanBay
        },
        'thoiGianDung1': {
            'choices': [('', 'None')] + [(str(i), str(i)) for i in range(20, 31)]
        },
        'thoiGianDung2': {
            'choices': [('', 'None')] + [(str(i), str(i)) for i in range(20, 31)]
        }
    }

    def on_model_change(self, form, model, is_created):
        if form.sanBayDi.data and form.sanBayDen.data:
            if form.sanBayDi.data == form.sanBayDen.data:
                raise ValidationError("Sân bay đến và đi không được trùng nhau")

        if form.sanBayTrungGian1.data and form.sanBayTrungGian2.data:
            if form.sanBayTrungGian1.data == form.sanBayTrungGian2.data:
                raise ValidationError("Hai sân bay trung gian không được trùng nhau")


        if form.sanBayDi.data == form.sanBayTrungGian1.data or form.sanBayDi.data == form.sanBayTrungGian2.data:
            raise ValidationError("Sân bay đi không được trùng với sân bay trung gian")


        if form.sanBayDen.data == form.sanBayTrungGian1.data or form.sanBayDen.data == form.sanBayTrungGian2.data:
            raise ValidationError("Sân bay đến không được trùng với sân bay trung gian")


        if form.sanBayTrungGian1.data and not form.thoiGianDung1.data:
            raise ValidationError("Vui lòng nhập thời gian dừng cho sân bay trung gian 1.")

        if form.sanBayTrungGian2.data and not form.thoiGianDung2.data:
            raise ValidationError("Vui lòng nhập thời gian dừng cho sân bay trung gian 2.")


        thoiGianDung1_data = form.thoiGianDung1.data
        model.thoiGianDung1 = int(thoiGianDung1_data) if thoiGianDung1_data and thoiGianDung1_data.isdigit() else None

        thoiGianDung2_data = form.thoiGianDung2.data
        model.thoiGianDung2 = int(thoiGianDung2_data) if thoiGianDung2_data and thoiGianDung2_data.isdigit() else None


        if form.sanBayTrungGian2.data and not form.sanBayTrungGian1.data:
            model.sanBayTrungGian1 = form.sanBayTrungGian2.data
            model.sanBayTrungGian2 = None
            model.thoiGianDung1 = model.thoiGianDung2
            model.thoiGianDung2 = None
            flash("Sân bay trung gian 2 đã được chuyển lên làm sân bay trung gian 1.", "info")


        if form.sanBayDi.data:
            model.maSanBayDi = form.sanBayDi.data.maSanBay
        if form.sanBayDen.data:
            model.maSanBayDen = form.sanBayDen.data.maSanBay
        if form.sanBayTrungGian1.data:
            model.maSanBayTrungGian1 = form.sanBayTrungGian1.data.maSanBay
        if form.sanBayTrungGian2.data:
            model.maSanBayTrungGian2 = form.sanBayTrungGian2.data.maSanBay


class SanBayAdmin(AdminView):
    column_list = ['maSanBay', 'tenSanBay']
    column_labels = dict(maSanBay='Mã Sân Bay', tenSanBay='Tên Sân Bay')
    form_columns = ['maSanBay','tenSanBay']
    can_export = True
    column_searchable_list = ['tenSanBay']
    column_filters = ['maSanBay', 'tenSanBay']
    page_size = 10


class MayBayAdmin(AdminView):
    column_list = ['maMayBay', 'tenMayBay', 'tongSoGhe']
    column_labels = dict(maMayBay='Mã Máy Bay', tenMayBay='Tên Máy Bay', tongSoGhe='Tổng Số Ghế', gheHang1='Ghế hạng 1', gheHang2='Ghế hạng 2')
    column_searchable_list = ['tenMayBay']
    form_columns = ['tenMayBay', 'tongSoGhe', 'gheHang1', 'gheHang2']
    can_export = True
    page_size = 10

    def on_model_change(self, form, model, is_created):
        if form.gheHang1.data + form.gheHang2.data != form.tongSoGhe.data:
            raise ValidationError("Tổng số ghế không khớp với ghế hạng 1 + ghế hạng 2")


class ChuyenBayAdmin(AdminView):
    column_list = ['maChuyenBay', 'tuyenBay', 'gioDi', 'gioDen', 'mayBay']
    column_labels = dict(maChuyenBay='Mã Chuyến Bay', tuyenBay='Tuyến Bay', gioDi='Giờ Đi', gioDen='Giờ Đến',
                         mayBay='Máy Bay', thoiGianBay='Thời gian bay ( DỰ KIẾN )')
    column_searchable_list = ['maChuyenBay']
    form_columns = ['tuyenBay', 'gioDi', 'thoiGianBay', 'mayBay']

    can_export = True

    column_formatters = {
        'tuyenBay': lambda v, c, m, p: m.tuyenBay.tenTuyenBay if m.tuyenBay else '',
        'mayBay': lambda v, c, m, p: m.mayBay.tenMayBay if m.mayBay else '',
        'gioDi': lambda v, c, m, p: m.gioDi.strftime("%H:%M, %d/%m/%Y") if m.gioDi else '',
        'gioDen': lambda v, c, m, p: m.gioDen.strftime("%H:%M, %d/%m/%Y") if m.gioDen else '',
    }

    form_overrides = {
        'tuyenBay': QuerySelectField,
        'mayBay': QuerySelectField,
        'gioDi': DateTimeField,
        'thoiGianBay': IntegerField,
    }

    form_args = {
        'tuyenBay': {
            'query_factory': lambda: TuyenBay.query.all(),
            'get_label': lambda x: x.tenTuyenBay,
            'get_pk': lambda x: x.maTuyenBay
        },
        'mayBay': {
            'query_factory': lambda: MayBay.query.all(),
            'get_label': lambda x: x.tenMayBay,
            'get_pk': lambda x: x.maMayBay
        }
    }

    def on_model_change(self, form, model, is_created):
        gio_di = form.gioDi.data
        thoi_gian_bay = form.thoiGianBay.data
        may_bay = form.mayBay.data

        if not gio_di:
            raise ValidationError("Vui lòng chọn giờ đi.")

        if gio_di <= datetime.now():
            raise ValidationError("Giờ đi phải sau hơn thời điểm hiện tại.")

        if thoi_gian_bay is None or thoi_gian_bay <= 0:
            raise ValidationError("Vui lòng nhập thời gian bay hợp lệ (lớn hơn 0).")
        if not may_bay:
            raise ValidationError("Vui lòng chọn máy bay.")

        gio_den = gio_di + timedelta(minutes=thoi_gian_bay)
        model.gioDen = gio_den

        existing_flights = ChuyenBay.query.filter(ChuyenBay.maMayBay == may_bay.maMayBay).all()
        if model.maChuyenBay:
            existing_flights = [flight for flight in existing_flights if flight.maChuyenBay != model.maChuyenBay]

        for flight in existing_flights:
            if not (gio_den <= flight.gioDi or gio_di >= flight.gioDen):
                raise ValidationError(
                    f"Máy bay '{may_bay.tenMayBay}' đã được sử dụng trong chuyến bay từ {flight.gioDi} đến {flight.gioDen}. Vui lòng chọn thời gian khác.")

        model.gioDi = gio_di
        model.mayBay = may_bay
        model.thoiGianBay = thoi_gian_bay

        db.session.add(model)
        db.session.commit()

        tong_so_ghe = may_bay.tongSoGhe
        ghe_thuong_gia = may_bay.gheHang1
        ghe_pho_thong = may_bay.gheHang2


        for i in range(ghe_thuong_gia):
            ghe = Ghe(tenGhe=f"{may_bay.tenMayBay}-{i + 1}", maChuyenbay=model.maChuyenBay, hangGhe='ThuongGia',
                      trangThai=False, maMayBay=may_bay.maMayBay)  # Ghế trống
            db.session.add(ghe)

        for i in range(ghe_pho_thong):
            ghe = Ghe(tenGhe=f"{may_bay.tenMayBay}-{i + ghe_thuong_gia + 1}", maChuyenbay=model.maChuyenBay,
                      hangGhe='PhoThong', trangThai=False, maMayBay=may_bay.maMayBay)  # Ghế trống
            db.session.add(ghe)

        db.session.commit()

        return super(ChuyenBayAdmin, self).on_model_change(form, model, is_created)

class VeAdmin(AdminView):
    column_list = ['maVe', 'tinhTrangVe', 'giaVe', 'maChuyenBay', 'maHangVe', 'maGhe', 'tenKhachHang']
    column_labels = dict(maVe='Mã Vé', tinhTrangVe='Tình Trạng Vé', giaVe='Giá Vé', maChuyenBay='Chuyến Bay',
                         maHangVe='Hạng Vé', maGhe='Ghế', tenKhachHang='Tên Khách Hàng')
    column_searchable_list = ['maVe']
    form_columns = ['tinhTrangVe', 'giaVe', 'maChuyenBay', 'maHangVe', 'maGhe', 'tenKhachHang']
    can_export = True
    can_edit = False
    can_delete = False
    can_create = False

    column_formatters = {
        'maChuyenBay': lambda v, c, m, p: m.chuyenBay if m.chuyenBay else '',
        'maHangVe': lambda v, c, m, p: m.hangVe.tenHangVe if m.hangVe else '',
        'maGhe': lambda v, c, m, p: m.ghe.tenGhe if m.ghe else '',
        'tenKhachHang': lambda v, c, m, p: m.tenKhachHang if m.tenKhachHang else '',
    }

    form_overrides = {
        'tinhTrangVe': SelectField,
        # 'giaVe': SelectField,
        'maChuyenBay': QuerySelectField,
        'maHangVe': QuerySelectField,
        'maGhe': QuerySelectField,
        'tenKhachHang': QuerySelectField
    }

    form_args = {
        'tinhTrangVe': {
            'choices': [
                ('Đã Bán', 'Đã Bán'),
                ('Đã Đặt', 'Đã Đặt'),

            ]
        },
        # 'giaVe': {
        #     'choices': TuyenBay.get(TuyenBay.giaCoBan),
        # },
        'maChuyenBay': {
            'query_factory': lambda: ChuyenBay.query.all(),
            'get_label': lambda x: x.maChuyenBay,
            'get_pk': lambda x: x.maChuyenBay
        },
        'maHangVe': {
            'query_factory': lambda: HangVe.query.all(),
            'get_label': lambda x: x.tenHangVe,
            'get_pk': lambda x: x.maHangVe
        },
        'maGhe': {
            'query_factory': lambda: Ghe.query.all(),
            'get_label': lambda x: x.tenGhe,
            'get_pk': lambda x: x.maGhe
        },
        'tenKhachHang': {
            'query_factory': lambda: KhachHang.query.all(),
            'get_label': lambda x: x.hoVaTen,
            'get_pk': lambda x: x.maKhachHang
        }
    }


class AuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.vaiTro.__eq__(VaiTro.QUANTRI)


class LogoutView(AuthenticatedView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')


class StatsView(AuthenticatedView):
    @expose('/')
    def index(self):
        return self.render('admin/stats.html')


# api cho thong ke bao cao
@app.route('/api/doanh-thu-tuyen-bay-theo-thang', methods=['get'])
@login_required
def lay_doanh_thu_tuyen_bay_theo_thang():
    month = request.args.get('month') if request.args.get('month') else datetime.now().month
    year = request.args.get('year') if request.args.get('year') else datetime.now().year

    # Lấy dữ liệu doanh thu và số chuyến bay
    doanh_thu_tuyen_bay = get_doanh_thu_tuyen_bay_theo_thang(month, year)
    so_chuyen_bay = get_so_chuyen_bay_cua_tuyen_bay_theo_thang(month, year)

    # Chuyển so_chuyen_bay thành dictionary để dễ tra cứu
    so_chuyen_bay_dict = {scb[0]: scb[1] for scb in so_chuyen_bay}

    # Kết hợp dữ liệu doanh thu và số chuyến bay
    data = []
    for tb in doanh_thu_tuyen_bay:
        ma_tuyen_bay = tb[0]
        ten_tuyen_bay = tb[1]
        doanh_thu = round(tb[2])
        so_luot_bay = so_chuyen_bay_dict.get(ma_tuyen_bay, 0)  # Mặc định là 0 nếu không tìm thấy

        data.append({
            "id": ma_tuyen_bay,
            "tenTuyenBay": ten_tuyen_bay,
            "doanhThu": doanh_thu,
            "soLuotBay": so_luot_bay
        })

    return jsonify(data)


@app.route('/api/nhan-vien-ban-theo-thang', methods=['get'])
@login_required
def lay_thong_ke_nhan_vien_theo_thang():
    month = request.args.get('month') if request.args.get('month') else datetime.now().month
    year = request.args.get('year') if request.args.get('year') else datetime.now().year

    # Lấy dữ liệu nhân viên bán vé
    nhan_vien_ban_ve = get_so_ve_nhan_vien_ban_theo_thang(month, year)

    data = []
    for nv in nhan_vien_ban_ve:
        ma_nhan_vien = nv[0]
        ten_nhan_vien = nv[1]
        so_ve_ban = nv[2]
        doanh_thu = round(nv[3])

        data.append({
            "id": ma_nhan_vien,
            "tenNhanVien": ten_nhan_vien,
            "soVeBan": so_ve_ban,
            "doanhThu": doanh_thu
        })

    return jsonify(data)


@app.route('/api/doanh-thu-theo-nam', methods=['get'])
@login_required
def lay_doanh_thu_theo_nam():
    year = request.args.get('year') if request.args.get('year') else datetime.now().year

    # Lấy dữ liệu doanh thu
    doanh_thu = get_doanh_thu_theo_nam(year)

    data = []
    for dt in doanh_thu:
        thang = dt[0]
        doanh_thu = round(dt[1])

        data.append({
            "thang": thang,
            "doanhThu": doanh_thu
        })

    return jsonify(data)


admin.add_view(SanBayAdmin(SanBay, db.session, name='Sân bay'))
admin.add_view(MayBayAdmin(MayBay, db.session, name='Máy bay'))
admin.add_view(NhanVienAdmin(NhanVien, db.session, name='Nhân viên'))
admin.add_view(KhachHangAdmin(KhachHang, db.session, name='Khách hàng'))
admin.add_view(ChuyenBayAdmin(ChuyenBay, db.session, name='Chuyến bay'))
admin.add_view(TuyenBayAdmin(TuyenBay, db.session, name='Tuyến bay'))
admin.add_view(VeAdmin(Ve, db.session, name='Vé'))
admin.add_view(StatsView(name='Thống kê'))
admin.add_view(LogoutView(name='Đăng xuất'))
