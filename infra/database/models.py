"""
EXPLICACIÓN: Modelos SQLAlchemy que mapean las entidades de dominio a tablas de BD.
Estos modelos NO contienen lógica de negocio, solo mapeo objeto-relacional.
Son la representación técnica de nuestras entidades de dominio.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, Text, ForeignKey, Enum, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

# Enums para mantener consistencia con el dominio
class UserRoleEnum(enum.Enum):
    ADMIN = "admin"
    VETERINARIAN = "veterinarian"
    RECEPTIONIST = "receptionist"
    ASSISTANT = "assistant"

class PetSpeciesEnum(enum.Enum):
    DOG = "dog"
    CAT = "cat"
    BIRD = "bird"
    RABBIT = "rabbit"
    HAMSTER = "hamster"
    OTHER = "other"

class PetGenderEnum(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class AppointmentStatusEnum(enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class AppointmentTypeEnum(enum.Enum):
    CONSULTATION = "consultation"
    VACCINATION = "vaccination"
    SURGERY = "surgery"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    GROOMING = "grooming"

# Nuevos enums para facturación e inventario
class InvoiceStatusEnum(enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class ProductStatusEnum(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"

class ProductTypeEnum(enum.Enum):
    MEDICATION = "medication"
    SUPPLY = "supply"
    EQUIPMENT = "equipment"
    SERVICE = "service"
    FOOD = "food"
    ACCESSORY = "accessory"

class StockMovementTypeEnum(enum.Enum):
    PURCHASE = "purchase"
    SALE = "sale"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    EXPIRED = "expired"
    DAMAGED = "damaged"

class UserModel(Base):
    """
    Modelo SQLAlchemy para usuarios del sistema.
    Mapea la entidad User a la tabla 'users'.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.RECEPTIONIST, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    created_appointments = relationship("AppointmentModel", back_populates="creator", foreign_keys="AppointmentModel.created_by")
    assigned_appointments = relationship("AppointmentModel", back_populates="veterinarian", foreign_keys="AppointmentModel.veterinarian_id")
    stock_movements = relationship("StockMovementModel", back_populates="created_by_user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"

class ClientModel(Base):
    """
    Modelo SQLAlchemy para clientes (propietarios de mascotas).
    Mapea la entidad Client a la tabla 'clients'.
    """
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=True, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    identification_number = Column(String(20), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    pets = relationship("PetModel", back_populates="owner", cascade="all, delete-orphan")
    invoices = relationship("InvoiceModel", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.first_name} {self.last_name}')>"

class PetModel(Base):
    """
    Modelo SQLAlchemy para mascotas.
    Mapea la entidad Pet a la tabla 'pets'.
    """
    __tablename__ = 'pets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    species = Column(Enum(PetSpeciesEnum), nullable=False, default=PetSpeciesEnum.OTHER, index=True)
    breed = Column(String(50), nullable=True)
    birth_date = Column(Date, nullable=True)
    gender = Column(Enum(PetGenderEnum), nullable=False, default=PetGenderEnum.UNKNOWN)
    color = Column(String(30), nullable=True)
    weight = Column(Float, nullable=True)
    microchip_number = Column(String(20), nullable=True, unique=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    owner = relationship("ClientModel", back_populates="pets")
    appointments = relationship("AppointmentModel", back_populates="pet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Pet(id={self.id}, name='{self.name}', species='{self.species.value}')>"

class AppointmentModel(Base):
    """
    Modelo SQLAlchemy para citas veterinarias.
    Mapea la entidad Appointment a la tabla 'appointments'.
    """
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    pet_id = Column(Integer, ForeignKey('pets.id'), nullable=False, index=True)
    veterinarian_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    appointment_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, nullable=False, default=30)
    appointment_type = Column(Enum(AppointmentTypeEnum), nullable=False, index=True)
    status = Column(Enum(AppointmentStatusEnum), nullable=False, default=AppointmentStatusEnum.SCHEDULED, index=True)
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relaciones
    pet = relationship("PetModel", back_populates="appointments")
    veterinarian = relationship("UserModel", back_populates="assigned_appointments", foreign_keys=[veterinarian_id])
    creator = relationship("UserModel", back_populates="created_appointments", foreign_keys=[created_by])
    invoices = relationship("InvoiceModel", back_populates="appointment")

    def __repr__(self):
        return f"<Appointment(id={self.id}, pet_id={self.pet_id}, date='{self.appointment_date}', status='{self.status.value}')>"

# Nuevos modelos para inventario
class CategoryModel(Base):
    """
    Modelo SQLAlchemy para categorías de productos.
    Mapea la entidad Category a la tabla 'categories'.
    """
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    parent = relationship("CategoryModel", remote_side=[id], backref="subcategories")
    products = relationship("ProductModel", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"

class ProductModel(Base):
    """
    Modelo SQLAlchemy para productos.
    Mapea la entidad Product a la tabla 'products'.
    """
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(50), nullable=False, unique=True, index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True, index=True)
    product_type = Column(Enum(ProductTypeEnum), nullable=False, index=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(ProductStatusEnum), nullable=False, default=ProductStatusEnum.ACTIVE, index=True)
    minimum_stock = Column(Integer, nullable=False, default=0)
    maximum_stock = Column(Integer, nullable=True)
    reorder_point = Column(Integer, nullable=False, default=0)
    supplier = Column(String(200), nullable=True)
    expiration_tracking = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    category = relationship("CategoryModel", back_populates="products")
    stocks = relationship("StockModel", back_populates="product", cascade="all, delete-orphan")
    stock_movements = relationship("StockMovementModel", back_populates="product")
    invoice_items = relationship("InvoiceItemModel", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"

class StockModel(Base):
    """
    Modelo SQLAlchemy para stock de productos.
    Mapea la entidad Stock a la tabla 'stock'.
    """
    __tablename__ = 'stock'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    current_quantity = Column(Integer, nullable=False, default=0)
    reserved_quantity = Column(Integer, nullable=False, default=0)
    expiration_date = Column(Date, nullable=True, index=True)
    batch_number = Column(String(50), nullable=True, index=True)
    location = Column(String(100), nullable=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    product = relationship("ProductModel", back_populates="stocks")

    def __repr__(self):
        return f"<Stock(id={self.id}, product_id={self.product_id}, quantity={self.current_quantity})>"

class StockMovementModel(Base):
    """
    Modelo SQLAlchemy para movimientos de stock.
    Mapea la entidad StockMovement a la tabla 'stock_movements'.
    """
    __tablename__ = 'stock_movements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    movement_type = Column(Enum(StockMovementTypeEnum), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    reference_id = Column(Integer, nullable=True, index=True)
    reference_type = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relaciones
    product = relationship("ProductModel", back_populates="stock_movements")
    created_by_user = relationship("UserModel", back_populates="stock_movements")

    def __repr__(self):
        return f"<StockMovement(id={self.id}, product_id={self.product_id}, type='{self.movement_type.value}', quantity={self.quantity})>"

# Nuevos modelos para facturación
class InvoiceModel(Base):
    """
    Modelo SQLAlchemy para facturas.
    Mapea la entidad Invoice a la tabla 'invoices'.
    """
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey('appointments.id'), nullable=True, index=True)
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    issue_date = Column(DateTime, nullable=False, index=True)
    due_date = Column(DateTime, nullable=False, index=True)
    status = Column(Enum(InvoiceStatusEnum), nullable=False, default=InvoiceStatusEnum.DRAFT, index=True)
    tax_percentage = Column(Numeric(5, 2), nullable=False, default=0.00)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    client = relationship("ClientModel", back_populates="invoices")
    appointment = relationship("AppointmentModel", back_populates="invoices")
    items = relationship("InvoiceItemModel", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', status='{self.status.value}')>"

class InvoiceItemModel(Base):
    """
    Modelo SQLAlchemy para elementos de factura.
    Mapea la entidad InvoiceItem a la tabla 'invoice_items'.
    """
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True, index=True)
    description = Column(String(500), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    discount_percentage = Column(Numeric(5, 2), nullable=False, default=0.00)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relaciones
    invoice = relationship("InvoiceModel", back_populates="items")
    product = relationship("ProductModel", back_populates="invoice_items")

    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, invoice_id={self.invoice_id}, description='{self.description}')>"

# Índices adicionales para optimización
from sqlalchemy import Index

# Índices compuestos para consultas frecuentes existentes
Index('idx_appointments_date_status', AppointmentModel.appointment_date, AppointmentModel.status)
Index('idx_appointments_vet_date', AppointmentModel.veterinarian_id, AppointmentModel.appointment_date)
Index('idx_pets_client_active', PetModel.client_id, PetModel.is_active)

# Nuevos índices para facturación e inventario
Index('idx_invoices_client_status', InvoiceModel.client_id, InvoiceModel.status)
Index('idx_invoices_date_status', InvoiceModel.issue_date, InvoiceModel.status)
Index('idx_invoices_due_date_status', InvoiceModel.due_date, InvoiceModel.status)
Index('idx_products_category_status', ProductModel.category_id, ProductModel.status)
Index('idx_products_type_status', ProductModel.product_type, ProductModel.status)
Index('idx_stock_product_expiration', StockModel.product_id, StockModel.expiration_date)
Index('idx_stock_movements_product_date', StockMovementModel.product_id, StockMovementModel.created_at)
Index('idx_stock_movements_type_date', StockMovementModel.movement_type, StockMovementModel.created_at)