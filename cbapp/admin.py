from datetime import datetime

# admin.py
from flask import app, flash, redirect
from flask_admin import Admin, expose, BaseView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form import Select2Widget, DateTimePickerWidget
from flask_login import current_user, logout_user
from werkzeug.security import generate_password_hash
from wtforms import Form, StringField, SelectField, form
from wtforms.fields.choices import SelectMultipleField
from wtforms.validators import DataRequired
from cbapp import app, db
from cbapp.models import NhanVien, KhachHang, ChuyenBay, TuyenBay, SanBay, MayBay, VaiTro
from flask_wtf import FlaskForm
from wtforms.validators import ValidationError
from flask_admin.contrib.sqla import ModelView
from wtforms import SelectField

admin = Admin(app=app, name='Quản trị chuyến bay', template_mode='bootstrap4')


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.vaiTro.__eq__(VaiTro.QUANTRI)


class NhanVienAdmin(AdminView):
    column_list = ['tenNhanVien', 'email', 'soDienThoai','vaiTro']
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
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.active = True

            if 'matKhau' in form and form.matKhau.data:
                model.matKhau = generate_password_hash(form.matKhau.data)
        super(KhachHangAdmin, self).on_model_change(form, model, is_created)


class TuyenBayAdmin(AdminView):
    form_columns = ['tenTuyenBay', 'sanBayDi', 'sanBayDen','giaCoBan', 'sanBayTrungGian1', 'thoiGianDung1', 'sanBayTrungGian2', 'thoiGianDung2']
    column_list = ['maTuyenBay', 'tenTuyenBay', 'maSanBayDi', 'maSanBayDen']
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
    form_columns = ['maSanBay','tenSanBay']
    can_export = True
    column_searchable_list = ['tenSanBay']
    column_filters = ['maSanBay', 'tenSanBay']
    page_size = 10


class MayBayAdmin(AdminView):
    column_list = ['maMayBay', 'tenMayBay', 'tongSoGhe']
    form_columns = ['tenMayBay', 'tongSoGhe', 'gheHang1', 'gheHang2']
    can_export = True
    page_size = 10

    def on_model_change(self, form, model, is_created):
        if form.gheHang1.data + form.gheHang2.data != form.tongSoGhe.data:
            raise ValidationError("Tổng số ghế không khớp với ghế hạng 1 + ghế hạng 2")


class ChuyenBayAdmin(AdminView):
    column_list = ['maChuyenBay', 'tuyenBay', 'gioDi', 'gioDen', 'mayBay']
    form_columns = ['tuyenBay', 'gioDi', 'gioDen', 'mayBay']
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
        if is_created:

            may_bay = form.mayBay.data
            gio_di = form.gioDi.data
            gio_den = form.gioDen.data

            if not may_bay:
                raise ValidationError("Vui lòng chọn máy bay.")
            if not gio_di or not gio_den:
                raise ValidationError("Vui lòng chọn giờ đi và giờ đến.")


            if gio_di >= gio_den:
                raise ValidationError("Giờ đi phải trước giờ đến.")




            existing_flights = ChuyenBay.query.filter(ChuyenBay.maMayBay == may_bay.maMayBay).all()


            if model.maChuyenBay:
                existing_flights = [flight for flight in existing_flights if flight.maChuyenBay != model.maChuyenBay]





            for flight in existing_flights:
                if not (gio_den <= flight.gioDi or gio_di >= flight.gioDen):
                    raise ValidationError(
                        f"Máy bay '{may_bay.tenMayBay}' đã được sử dụng trong chuyến bay từ {flight.gioDi} đến {flight.gioDen}. Vui lòng chọn thời gian khác.")


            model.gioDi = gio_di
            model.gioDen = gio_den
            model.mayBay = may_bay


        return super(ChuyenBayAdmin, self).on_model_change(form, model, is_created)


class AuthenticatedView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated


class LogoutView(AuthenticatedView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')


class StatsView(AuthenticatedView):
    @expose('/')
    def index(self):
        nhanVien = NhanVien.query.count()
        khackHang = KhachHang.query.count()

        return self.render('admin/stats.html', nhanVien=nhanVien, khachHang=khackHang)


admin.add_view(SanBayAdmin(SanBay, db.session, name='Sân bay'))
admin.add_view(MayBayAdmin(MayBay, db.session, name='Máy bay'))
admin.add_view(NhanVienAdmin(NhanVien, db.session, name='Nhân viên'))
admin.add_view(KhachHangAdmin(KhachHang, db.session, name='Khách hàng'))
admin.add_view(ChuyenBayAdmin(ChuyenBay, db.session, name='Chuyến bay'))
admin.add_view(TuyenBayAdmin(TuyenBay, db.session, name='Tuyến bay'))
admin.add_view(StatsView(name='Thống kê'))
admin.add_view(LogoutView(name='Đăng xuất'))
