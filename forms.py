"""Forms for the application."""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, IntegerField, SelectField, PasswordField, EmailField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, URL, ValidationError
from slugify import slugify

class SystemSettingsForm(FlaskForm):
    """Form for system settings."""
    accessibility_menu_enabled = BooleanField('ACCESSIBILITY MENU')
    maintenance_mode = BooleanField('MAINTENANCE MODE')
    registration_enabled = BooleanField('ENABLE REGISTRATION')

class DAGForm(FlaskForm):
    """Form for DAG creation."""
    name = StringField('NAME', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('DESCRIPTION', validators=[DataRequired()])
    type = SelectField('TYPE', choices=[
        ('research', 'RESEARCH'),
        ('development', 'DEVELOPMENT'),
        ('community', 'COMMUNITY')
    ])

class PointsAllocationForm(FlaskForm):
    """Form for points allocation."""
    username = StringField('USERNAME', validators=[DataRequired()])
    amount = IntegerField('AMOUNT', validators=[DataRequired()])
    reason = TextAreaField('REASON', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    """Form for user registration."""
    username = StringField('USERNAME', validators=[
        DataRequired(),
        Length(min=3, message='Username must be at least 3 characters long')
    ])
    email = EmailField('EMAIL', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('PASSWORD', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    referral_code = StringField('REFERRAL CODE', validators=[Optional()])
    terms = BooleanField('Terms', validators=[DataRequired(message='You must accept the terms')])

class ChannelForm(FlaskForm):
    """Form for creating and editing channels."""
    name = StringField('Channel Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    channel_type = SelectField('Channel Type', choices=[
        ('ecosystem', 'Ecosystem Channel'),
        ('dag', 'DAG Channel'),
        ('personal', 'Personal Channel')
    ], validators=[DataRequired()])
    visibility = SelectField('Visibility', choices=[
        ('public_world', 'Public - Anyone can view'),
        ('public_da', 'DA Members Only'),
        ('private_dag', 'Private - DAG Members Only')
    ], validators=[DataRequired()])
    dag_id = SelectField('DAG', coerce=int, validators=[Optional()])
    banner = FileField('Banner Image')
    icon = FileField('Channel Icon')
    
    def validate_name(self, field):
        """Validate that the channel name is unique."""
        from models import Channel
        # Check if channel name already exists
        slug = slugify(field.data)
        existing = Channel.query.filter_by(slug=slug).first()
        if existing:
            raise ValidationError('A channel with this name already exists.')

class PostForm(FlaskForm):
    """Form for creating and editing posts."""
    title = StringField('Title', validators=[Optional(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    post_type = SelectField('Post Type', choices=[
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('link', 'Link'),
        ('poll', 'Poll')
    ], validators=[DataRequired()])
    media = FileField('Media')
    external_url = StringField('External URL', validators=[Optional(), URL()])

class CommentForm(FlaskForm):
    """Form for adding comments to posts."""
    content = TextAreaField('Comment', validators=[DataRequired(), Length(max=1000)])
    parent_id = HiddenField('Parent Comment ID')