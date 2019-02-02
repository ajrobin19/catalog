from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }


class Department(Base):
    __tablename__ = 'department'
   
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serializable(self):
       """Return object data in easily serializeable format"""
       return {
           'name'         : self.name,
           'id'           : self.id,
       }
 
class DepartmentItem(Base):
    __tablename__ = 'department_item'


    name = Column(String(80), nullable = False)
    id = Column(Integer, primary_key = True)
    description = Column(String(250))
    price = Column(String(8))
    department_id = Column(Integer,ForeignKey('department.id'))
    department = relationship(Department, backref='items')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


    @property
    def serializable(self):
       """Return object data in easily serializeable format"""
       return {
           'name' : self.name,
           'description' : self.description,
           'department_id': self.department_id,
           'id' : self.id,
           'price' : self.price,
       }



engine = create_engine('sqlite:///catalog.db')
 

Base.metadata.create_all(engine)
