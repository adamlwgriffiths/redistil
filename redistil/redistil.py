from inspect import isclass
from datetime import date, datetime
from cerberus import Validator, TypeDefinition
from ipaddress import IPv4Address, IPv6Address
from .pipeline import PromisePipeline

def register_types_mapping(data):
    Validator.types_mapping.update(data)


class FieldBase:
    schema = None

    def __init__(self, type, **kwargs):
        self.type = type() if isclass(type) else type
        self.owner = None
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner
        self.type.__set_name__(owner, name)

    def __set__(self, instance, value):
        value = self.type.set(instance, value)
        instance._data[self.name] = value

    def __get__(self, instance, value):
        # instance is null when the field is being accessed via the class, not an object
        # Ie MyModel.MyField
        if not instance:
            return self

        value = instance._data.get(self.name)
        value = self.type.get(instance, value)
        # update the value incase it changed
        instance._data[self.name] = value
        return value

    def to_db(self, value):
        return self.type.to_db(value)

    def from_db(self, value):
        return self.type.from_db(value)

    def save(self, key, field, data):
        raise NotImplementedError

    def load(self, key, field):
        raise NotImplementedError


class Field(FieldBase):
    def __init__(self, type, primary_key=False, **kwargs):
        super().__init__(type, **kwargs)
        self.schema = {**self.type.schema, **kwargs}

        self.primary_key = primary_key
        if self.primary_key:
            self.schema['required'] = True

    def save(self, db, key, field, value):
        db.hset(key, field, value)

    def load(self, db, key, field):
        return db.hget(key, field)

    def delete(self, db, key, field):
        return None

    def field(self, key):
        return self.name


class Container(FieldBase):
    def __init__(self, type, **kwargs):
        if type.schema['type'] in ['list', 'set', 'dict']:
            raise TypeError('Container fields are not nestable')
        super().__init__(type, **kwargs)
        self.schema = {**self.schema, **kwargs}
        self.schema['schema'] = self.type.schema

    def delete(self, db, key, field):
        db.delete(self.key(key))

    def key(self, key):
        return f'{key}::{self.name}'


class List(Container):
    schema = {'type': 'list'}

    def replace_list(self, db, key, data):
        db.delete(key)
        for value in data:
            db.rpush(key, value)

    def set(self, instance, value):
        return [self.type.set(instance, item) for item in value]

    def get(self, instance, value):
        return [self.type.get(instance, item) for item in value] if value else None

    def save(self, db, key, field, value):
        self.replace_list(db, self.key(key), value)

    def load(self, db, key, field):
        return db.lrange(self.key(key), 0, -1)

    def to_db(self, value):
        return [self.type.to_db(x) for x in value]

    def from_db(self, value):
        return [self.type.from_db(x) for x in value]



class Set(Container):
    schema = {'type': 'set'}

    def replace_set(self, db, key, data):
        db.delete(key)
        for value in data:
            db.sadd(key, value)

    def save(self, db, key, field, value):
        self.replace_set(db, self.key(key), value)

    def load(self, db, key, field):
        return db.smembers(self.key(key))

    def set(self, instance, value):
        return {self.type.set(instance, item) for item in value}

    def get(self, instance, value):
        return {self.type.get(instance, item) for item in value} if value else None

    def to_db(self, value):
        return {self.type.to_db(x) for x in value}

    def from_db(self, value):
        return {self.type.from_db(x) for x in value}

# Dict type not provided as they can just be flattened into the Model
# or a secondary Model can be referenced




class TypeMeta(type):
    def __new__(metacls, name, bases, namespace, **kwargs):
        if 'types_mapping' in namespace:
            register_types_mapping(namespace['types_mapping'])
        return super().__new__(metacls, name, bases, namespace, **kwargs)


class Type(object, metaclass=TypeMeta):
    schema = None
    to_db = lambda self, value: value
    from_db = lambda self, value: value

    def __init__(self, **kwargs):
        self.schema.update(**kwargs)
        self.owner = None
        self.name = None

    def __set_name__(self, owner, name):
        self.owner = owner
        self.name = name

    def set(self, instance, value):
        return value

    def get(self, instance, value):
        return value

    def key_field(self, key):
        return self.owner.key(key), self.name

class Boolean(Type):
    schema = {'type': 'boolean'}
    to_db = lambda self, value: int(value)
    from_db = lambda self, value: bool(int(value.decode('utf-8')))

class Binary(Type):
    schema = {'type': 'binary'}

class Date(Type):
    schema = {'type': 'date'}
    to_db = lambda self, value: value.isoformat()
    from_db = lambda self, value: date.fromisoformat(value.decode('utf-8'))

class DateTime(Type):
    schema = {'type': 'datetime'}
    to_db = lambda self, value: value.isoformat()
    from_db = lambda self, value: datetime.fromisoformat(value.decode('utf-8'))

class Float(Type):
    schema = {'type': 'float'}
    from_db = lambda self, value: float(value)

class Integer(Type):
    schema = {'type': 'integer'}
    from_db = lambda self, value: int(value)

class Number(Type):
    schema = {'type': 'number'}
    from_db = lambda self, value: float(value)

class String(Type):
    schema = {'type': 'string'}
    from_db = lambda self, value: value.decode('utf-8')

class EmailAddress(String):
    EMAIL_REGEX = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    schema = {'type': 'string', 'regex': EMAIL_REGEX}

class IPAddress(Type):
    schema = {'type': 'ipaddress'}
    types_mapping = {'ipaddress': TypeDefinition('ipaddress', (IPv4Address, IPv6Address), ())}
    to_db = lambda self, value: str(value)
    from_db = lambda self, value: ip_address(value.decode('utf-8'))

class IPV4Address(Type):
    schema = {'type': 'ipv4address'}
    types_mapping = {'ipv4address': TypeDefinition('ipv4address', (IPv4Address,), ())}
    to_db = lambda self, value: str(value)
    from_db = lambda self, value: IPv4Address(value.decode('utf-8'))

class IPV6Address(Type):
    schema = {'type': 'ipv6address'}
    types_mapping = {'ipv6address': TypeDefinition('ipv6address', (IPv6Address,), ())}
    to_db = lambda self, value: str(value)
    from_db = lambda self, value: IPv6Address(value.decode('utf-8'))



class ModelMeta(type):
    def __new__(metacls, name, bases, namespace, **kwargs):
        def discover_fields():
            return {k:v for k,v in namespace.items() if isinstance(v, FieldBase)}
        def determine_primary_key(fields):
            # ensure we have exactly one primary key
            # don't do this check for the base Model class
            if name != 'Model':
                # filter fields that cant be primary keys
                fields = {k:v for k, v in fields.items() if isinstance(v, Field)}
                primary_keys = [field_name for field_name, field in fields.items() if field.primary_key]
                if len(primary_keys) != 1:
                    raise TypeError(f'{name} must have one field specified as primary_key')
                return primary_keys[0]
        def create_schema():
            return {name: field.schema for name, field in fields.items()}
        def register_model_(cls):
            if name != 'Model':
                register_model(cls)

        fields = discover_fields()
        namespace['_fields'] = fields
        namespace['_primary_key'] = determine_primary_key(fields)
        namespace['_schema'] = create_schema()

        return super().__new__(metacls, name, bases, namespace, **kwargs)

class Model(object, metaclass=ModelMeta):
    class Validator(Validator):
        # cerberus helpers for common normalize/coerce functions
        def _normalize_default_setter_utcnow(self, document):
            return datetime.utcnow()

    @classmethod
    def create(cls, db, **values):
        obj = cls(**values)
        # assert that the primary key is set
        if obj.id is None:
            raise ValueError('Primary key not set')
        obj.save(db)
        return obj

    @classmethod
    def key(cls, id):
        return f'{cls.__name__}::{id}'

    @classmethod
    def primary_key(cls):
        return cls._primary_key

    @classmethod
    def load(cls, db, id, *fields):
        # always load the primary key directly from the requested id
        obj = cls(**{cls.primary_key(): id})
        obj.load_fields(db, *fields)
        return obj

    def __init__(self, **values):
        self._data = {}
        for k,v in values.items():
            setattr(self, k, v)

    @property
    def id(self):
        return self._data.get(self.primary_key())

    @property
    def redis_key(self):
        primary_field = self._fields.get(self.primary_key())
        id_ = primary_field.type.to_db(self.id)
        return self.key(id_)

    @property
    def schema(self):
        return self._schema

    def load_fields(self, db, *fields):
        def loader(field_name):
            return self._fields.get(field_name).load
        def py_value(field_name, value):
            fn = self._fields.get(field_name).from_db
            return fn(value)

        # ensure the id is db friendly
        key = self.redis_key
        field_names = {field.name for field in fields} if fields else self._schema.keys()

        # create a pipeline and get the values all at once
        p = PromisePipeline(db)
        values = {name: loader(name)(p, key, name) for name in field_names}
        p.execute()

        # dereference the promises
        # filter Nones and cast from db
        values = {k: py_value(k, v.value) for k, v in values.items() if v.value is not None}

        for k,v in values.items():
            setattr(self, k, v)

    def validate(self, field_names):
        schema = {k:v for k,v in self._schema.items() if k in field_names}
        data = {k:v for k,v in self._data.items() if k in field_names}
        validator = self.Validator(schema)
        document = validator.normalized(data)
        if not validator(document):
            raise ValueError(str(validator.errors))
        return document

    def save(self, db, *fields):
        def redis_key():
            primary_field = self._fields.get(self.primary_key())
            id_ = primary_field.type.to_db(self.id)
            return self.key(id_)
        def saver(field_name):
            return self._fields.get(field_name).save
        def db_value(field_name, value):
            fn = self._fields.get(field_name).to_db
            return fn(value)

        key = self.redis_key
        field_names = {field.name for field in fields} if fields else self._schema.keys()
        # normalise and validate
        data = self.validate(field_names)

        p = PromisePipeline(db, transaction=True)
        for field_name in field_names:
            value = data.get(field_name)
            if value is None:
                continue
            value = db_value(field_name, value)
            saver(field_name)(p, key, field_name, value)
        p.execute()

    def delete(self, db):
        def deleter(field_name):
            return self._fields.get(field_name).delete

        key = self.redis_key
        field_names = self._schema.keys()

        p = PromisePipeline(db)
        # delete each field incase they have a custom deleter
        # then delete ourself
        for name in field_names:
            deleter(name)(p, key, name)
        p.delete(key)
        p.execute()

    def __str__(self):
        return f"<class '{__name__}.{self.__class__.__name__}'>"

    def __repr__(self):
        # sort by the ordering of our fields, not the order things were assigned
        values = {k:self._data.get(k) for k in self._fields.keys()}
        args = ', '.join(f'{k}={v}' for k,v in values.items())
        return f'{self.__class__.__name__}({args})'
