from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import stripe
import os
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = FastAPI()

# Initialize Stripe
stripe.api_key = "your_stripe_secret_key"  # Replace with your Stripe secret key

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:////app/marketplace.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    image_url = Column(String)
    stripe_price_id = Column(String)

Base.metadata.create_all(bind=engine)

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    image_url: str

class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: float
    image_url: str

@app.post("/products/", response_model=ProductResponse)
async def create_product(product: ProductCreate):
    # Create Stripe product
    stripe_product = stripe.Product.create(
        name=product.name,
        description=product.description,
    )
    
    stripe_price = stripe.Price.create(
        product=stripe_product.id,
        unit_amount=int(product.price * 100),  # Convert to cents
        currency="usd",
    )
    
    db = SessionLocal()
    db_product = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        image_url=product.image_url,
        stripe_price_id=stripe_price.id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[ProductResponse])
async def get_products():
    db = SessionLocal()
    products = db.query(Product).all()
    return products

@app.post("/create-checkout-session/{product_id}")
async def create_checkout_session(product_id: int):
    db = SessionLocal()
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': product.stripe_price_id,
            'quantity': 1,
        }],
        mode='payment',
        success_url='http://localhost:8501/success',
        cancel_url='http://localhost:8501/cancel',
    )
    
    return {"checkout_url": checkout_session.url}

# Add some dummy products
@app.post("/add-dummy-products")
async def add_dummy_products():
    dummy_products = [
        {
            "name": "Plant Disease Detection Kit",
            "description": "Professional kit for plant disease detection",
            "price": 99.99,
            "image_url": "https://example.com/kit.jpg"
        },
        {
            "name": "Garden Health Monitor",
            "description": "24/7 garden monitoring system",
            "price": 149.99,
            "image_url": "https://example.com/monitor.jpg"
        },
        {
            "name": "Plant Care Guide",
            "description": "Comprehensive guide for plant care",
            "price": 29.99,
            "image_url": "https://example.com/guide.jpg"
        }
    ]
    
    db = SessionLocal()
    for product_data in dummy_products:
        if not db.query(Product).filter(Product.name == product_data["name"]).first():
            await create_product(ProductCreate(**product_data))
    
    return {"message": "Dummy products added successfully"}