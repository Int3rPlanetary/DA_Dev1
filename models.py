"""Models for the application."""
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import db

# Many-to-many relationship between users and channels they follow
channel_followers = Table('channel_followers', db.Model.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('channel_id', Integer, ForeignKey('channels.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """User model with essential fields for authentication."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(256), nullable=True)
    account_type = Column(String(20), default='member')
    notification_settings = Column(String(20), default='important')
    privacy_level = Column(String(20), default='public')
    language = Column(String(10), default='en')
    referral_code = Column(String(20), unique=True, nullable=True)
    referral_count = Column(Integer, default=0)
    referral_points = Column(Integer, default=0)
    network_rank = Column(String(20), default='Novice')

    # Relationships
    achievements = relationship('Achievement', backref='user', lazy=True)
    dag_memberships = relationship('DAGMembership', backref='user', lazy=True)
    listings = relationship('Listing', backref='author', lazy=True)
    created_projects = relationship('Project', backref='project_owner', lazy=True)
    
    # Social network relationships
    posts = relationship('Post', backref='author', lazy=True)
    comments = relationship('Comment', backref='author', lazy=True)
    reactions = relationship('Reaction', backref='user', lazy=True)
    owned_channels = relationship('Channel', backref='owner', lazy=True)
    followed_channels = relationship('Channel', secondary=channel_followers, 
                                    backref=db.backref('followers', lazy='dynamic'))

    def get_id(self):
        """Return the user ID as a string."""
        return str(self.id)

class Achievement(db.Model):
    """Achievement model for tracking user accomplishments."""
    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)
    achievement_type = Column(String(50), nullable=False)
    points_awarded = Column(Integer, default=0)

class DAGMembership(db.Model):
    """Model for tracking user memberships in DAGs."""
    __tablename__ = 'dag_memberships'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    dag_id = Column(Integer, ForeignKey('dag.id'), nullable=False)
    role = Column(String(20), default='member')  # member, admin, moderator
    joined_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='active')  # active, inactive, suspended

class Project(db.Model):
    """Project model."""
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)  # 'backlog', 'wip', 'blocked', 'done'
    funding_goal = Column(Integer, nullable=False)  # Amount in DAPs
    current_funding = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    votes = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Relationships
    supporters = relationship('ProjectSupport', backref='project', lazy=True)

class ProjectSupport(db.Model):
    __tablename__ = 'project_supports'
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Integer, nullable=False)  # Amount in DAPs
    created_at = Column(DateTime, default=datetime.utcnow)

    # Unique constraint to prevent duplicate support
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id', name='uix_project_support'),)

class Listing(db.Model):
    """Enhanced listing model with all metadata."""
    __tablename__ = 'listings'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    type = Column(String(20), nullable=False)  # physical, digital, investment, charity, crowdfunding
    status = Column(String(20), default='active')  # active, pending, sold, expired
    price = Column(Float, nullable=True)
    currency = Column(String(3), default='DAP')
    views = Column(Integer, default=0)
    visibility = Column(String(20), default='public_world')  # public_world, public_da, private_dag
    creator_type = Column(String(20), default='member')  # member, dag, da

    # For investment/charity/crowdfunding listings
    target_amount = Column(Float, nullable=True)
    current_amount = Column(Float, default=0)
    end_date = Column(DateTime, nullable=True)

    # DAG-specific listing
    dag_id = Column(Integer, ForeignKey('dag.id'), nullable=True)

class SystemSettings(db.Model):
    """System settings model."""
    __tablename__ = 'system_settings'
    id = Column(Integer, primary_key=True)
    accessibility_menu_enabled = Column(Boolean, default=False)
    maintenance_mode = Column(Boolean, default=False)
    registration_enabled = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def get_settings():
        """Get or create system settings."""
        settings = SystemSettings.query.first()
        if not settings:
            settings = SystemSettings()
            db.session.add(settings)
            db.session.commit()
        return settings

class PasswordReset(db.Model):
    """Password reset model."""
    __tablename__ = 'password_resets'
    id = Column(Integer, primary_key=True)
    email = Column(String(120), nullable=False)
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used = Column(Boolean, default=False)

class Shop(db.Model):
    __tablename__ = 'shops'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=False)  # Requires admin approval
    status = Column(String(20), default='pending')  # pending, approved, suspended

    # Relationships
    owner = relationship('User', foreign_keys=[owner_id])
    products = relationship('Product', backref='shop', lazy=True)

    @property
    def product_count(self):
        return len(self.products)

class Connection(db.Model):
    __tablename__ = 'connections'
    id = Column(Integer, primary_key=True)
    initiator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    connection_type = Column(String(20), nullable=False)  # 'referral', 'transaction', 'dag_member'
    strength = Column(Integer, default=1)  # Represents connection strength based on interactions
    created_at = Column(DateTime, default=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)  # Price in DAPs
    seller_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    type = Column(String(20), nullable=False)  # 'physical' or 'digital'
    visibility = Column(String(20), default='public_world')  # 'public_world', 'public_da', 'private_dag'
    dag_id = Column(Integer, ForeignKey('dag.id'), nullable=True)  # Only required for private_dag visibility
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=True)

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    goal = Column(Integer, nullable=False)  # Goal in DAPs
    current_amount = Column(Integer, default=0)
    creator_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    type = Column(String(20), nullable=False)  # 'charity', 'investment', or 'crowdfunding'
    visibility = Column(String(20), default='public_world')  # 'public_world', 'public_da', 'private_dag'
    dag_id = Column(Integer, ForeignKey('dag.id'), nullable=True)  # Only required for private_dag visibility

class DAG(db.Model):
    """DAG model for organizing community projects and activities."""
    __tablename__ = 'dag'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    type = Column(String(20), nullable=True)  # research, development, community
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    member_count = Column(Integer, default=0)
    status = Column(String(20), default='active')  # active, inactive, archived

    # Relationships
    listings = relationship('Listing', backref='dag', lazy=True)
    products = relationship('Product', backref='dag', lazy=True)
    campaigns = relationship('Campaign', backref='dag', lazy=True)
    members = relationship('DAGMembership', backref='dag', lazy=True)
    channels = relationship('Channel', backref='dag', lazy=True)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    type = Column(String(20), nullable=False)  # 'purchase', 'transfer', 'sale', 'funding'
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)  # 'DAP' or 'USD'
    status = Column(String(20), nullable=False)  # 'pending', 'completed', 'failed'
    description = Column(Text)
    reference = Column(String(255))  # For external references (e.g., Stripe charge ID)
    created_at = Column(DateTime, default=datetime.utcnow)

class Channel(db.Model):
    """Channel model for organizing content in the social network."""
    __tablename__ = 'channels'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    slug = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    channel_type = Column(String(20), nullable=False)  # 'ecosystem', 'dag', 'personal'
    visibility = Column(String(20), nullable=False)  # 'public_world', 'public_da', 'private_dag'
    dag_id = Column(Integer, ForeignKey('dag.id'), nullable=True)  # Only required for DAG channels
    is_featured = Column(Boolean, default=False)
    is_official = Column(Boolean, default=False)
    banner_url = Column(String(256), nullable=True)
    icon_url = Column(String(256), nullable=True)
    
    # Relationships
    posts = relationship('Post', backref='channel', lazy=True)
    moderators = relationship('ChannelModerator', backref='channel', lazy=True)
    
    @property
    def follower_count(self):
        return self.followers.count()
    
    @property
    def post_count(self):
        return len(self.posts)

class ChannelModerator(db.Model):
    """Model for tracking channel moderators."""
    __tablename__ = 'channel_moderators'
    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(20), default='moderator')  # 'moderator', 'admin'
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicate moderators
    __table_args__ = (db.UniqueConstraint('channel_id', 'user_id', name='uix_channel_moderator'),)

class Post(db.Model):
    """Post model for social network content."""
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    title = Column(String(200), nullable=True)  # Optional for some post types
    content = Column(Text, nullable=True)  # Text content
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    post_type = Column(String(20), nullable=False)  # 'text', 'image', 'video', 'article', 'link', 'poll'
    status = Column(String(20), default='published')  # 'published', 'draft', 'archived', 'deleted'
    view_count = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Media-specific fields
    media_url = Column(String(256), nullable=True)  # URL for image, video, etc.
    media_type = Column(String(20), nullable=True)  # 'image', 'video', 'audio', etc.
    thumbnail_url = Column(String(256), nullable=True)  # Thumbnail for videos
    
    # Article-specific fields
    excerpt = Column(Text, nullable=True)  # Short preview for articles
    reading_time = Column(Integer, nullable=True)  # Estimated reading time in minutes
    
    # Link-specific fields
    external_url = Column(String(256), nullable=True)  # External URL for link posts
    
    # Poll-specific fields
    poll_ends_at = Column(DateTime, nullable=True)  # End time for polls
    
    # Relationships
    comments = relationship('Comment', backref='post', lazy=True)
    reactions = relationship('Reaction', backref='post', lazy=True)
    poll_options = relationship('PollOption', backref='post', lazy=True)
    
    @property
    def comment_count(self):
        return len(self.comments)
    
    @property
    def reaction_count(self):
        return len(self.reactions)

class Comment(db.Model):
    """Comment model for posts."""
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    parent_id = Column(Integer, ForeignKey('comments.id'), nullable=True)  # For nested comments
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default='published')  # 'published', 'deleted', 'hidden'
    
    # Relationships
    replies = relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy=True)
    reactions = relationship('Reaction', backref='comment', lazy=True)
    
    @property
    def reaction_count(self):
        return len(self.reactions)

class Reaction(db.Model):
    """Reaction model for posts and comments."""
    __tablename__ = 'reactions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=True)
    comment_id = Column(Integer, ForeignKey('comments.id'), nullable=True)
    reaction_type = Column(String(20), nullable=False)  # 'like', 'love', 'haha', 'wow', 'sad', 'angry'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Ensure a user can only react once to a post or comment
    __table_args__ = (
        db.UniqueConstraint('user_id', 'post_id', name='uix_user_post_reaction'),
        db.UniqueConstraint('user_id', 'comment_id', name='uix_user_comment_reaction'),
        db.CheckConstraint('(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)', 
                          name='chk_reaction_target')
    )

class PollOption(db.Model):
    """Poll option model for poll posts."""
    __tablename__ = 'poll_options'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey('posts.id'), nullable=False)
    text = Column(String(200), nullable=False)
    position = Column(Integer, nullable=False)  # Order of options
    
    # Relationships
    votes = relationship('PollVote', backref='option', lazy=True)
    
    @property
    def vote_count(self):
        return len(self.votes)

class PollVote(db.Model):
    """Poll vote model for tracking user votes on polls."""
    __tablename__ = 'poll_votes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    option_id = Column(Integer, ForeignKey('poll_options.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Ensure a user can only vote once per poll
    __table_args__ = (db.UniqueConstraint('user_id', 'option_id', name='uix_user_option_vote'),)