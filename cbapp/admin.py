
# admin.py
from flask import app
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_admin.form import Select2Widget
from wtforms import Form, StringField, SelectField
from wtforms.fields.choices import SelectMultipleField
from wtforms.validators import DataRequired
from cbapp import app, db
from cbapp.models import NhanVien, KhachHang, ChuyenBay, TuyenBay, SanBay

admin = Admin(app=app, name='Quản trị chuyến bay', template_mode='bootstrap4')


class NhanVienAdmin(ModelView):
    def is_accessible(self):
        return True


class KhachHangAdmin(ModelView):
    def is_accessible(self):
        return True


class ChuyenBayAdmin(ModelView):
    def is_accessible(self):
        return True


class TuyenBayAdmin(ModelView):
    form_columns = ['tenTuyenBay', 'maSanBayDi', 'maSanBayDen', 'sanBayTrungGian']
    column_list = ['maTuyenBay', 'tenTuyenBay', 'maSanBayDi', 'maSanBayDen']
    can_export = True
    column_searchable_list = ['tenTuyenBay']
    column_filters = ['maTuyenBay', 'tenTuyenBay']
    page_size = 10

    # Sử dụng QuerySelectField để tạo dropdown cho mã Sân bay
    form_overrides = {
        'maSanBayDi': QuerySelectField,
        'maSanBayDen': QuerySelectField
    }

    # Định nghĩa cách lấy dữ liệu cho các trường 'maSanBayDi' và 'maSanBayDen'
    form_args = {
        'maSanBayDi': {
            'query_factory': lambda: SanBay.query.all(),  # Lấy tất cả các sân bay
            'get_label': lambda x: x.tenSanBay  # Hiển thị tên sân bay
        },
        'maSanBayDen': {
            'query_factory': lambda: SanBay.query.all(),  # Lấy tất cả các sân bay
            'get_label': lambda x: x.tenSanBay  # Hiển thị tên sân bay
        }
    }

    # Cải thiện giao diện người dùng bằng cách sử dụng Select2 cho các trường Select
    form_widget_args = {
        'maSanBayDi': {
            'widget': Select2Widget()
        },
        'maSanBayDen': {
            'widget': Select2Widget()
        }
    }




class SanBayAdmin(ModelView):
    column_list = ['maSanBay', 'tenSanBay']
    form_columns = ['tenSanBay']
    can_export = True
    column_searchable_list = ['tenSanBay']
    column_filters = ['maSanBay', 'tenSanBay']
    page_size = 10


admin.add_view(SanBayAdmin(SanBay, db.session))
admin.add_view(NhanVienAdmin(NhanVien, db.session))
admin.add_view(KhachHangAdmin(KhachHang, db.session))
admin.add_view(ChuyenBayAdmin(ChuyenBay, db.session))
admin.add_view(TuyenBayAdmin(TuyenBay, db.session))
