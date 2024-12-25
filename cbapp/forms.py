from flask_wtf import FlaskForm
from wtforms.fields.simple import PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired, Length, EqualTo, Email


class ChangePasswordForm(FlaskForm):
    mat_khau_cu = PasswordField('Mật khẩu cũ', validators=[DataRequired()])
    mat_khau_moi = PasswordField('Mật khẩu mới', validators=[DataRequired(), Length(min=8)])
    xac_nhan_mat_khau = PasswordField('Xác nhận mật khẩu mới', validators=[DataRequired(), EqualTo('mat_khau_moi')])
    submit = SubmitField('Đổi Mật Khẩu')

class ChangeInfoForm(FlaskForm):
    ho_va_ten = StringField('Họ và tên', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    so_dien_thoai = StringField('Số điện thoại', validators=[DataRequired()])
    tai_khoan = StringField('Tài khoản', validators=[DataRequired()])
    cccd = StringField('CCCD', validators=[DataRequired()])
    submit = SubmitField('Cập nhật thông tin')
