# Redistil

![logo](https://raw.githubusercontent.com/adamlwgriffiths/redistil/master/images/redistil.jpg)

Declarative data types using [Cerberus](https://github.com/pyeve/cerberus) for schemas, optimised for Redis.

This codebase is similar to [Modulus](https://github.com/adamlwgriffiths/modulus), except it is far simpler
and features optimisations for Redis that preserve the simple key/value nature of it - specifically selective loading and saving of fields.


## Features

* Declarative data model
* Cerberus schemas remove the need for bytes->string encode/decode
* Simple implementation
* Selective loading/saving of Fields
* Saving / Loading use Redis pipelines for performance
* Extensible to new datatypes


## Installation

    $ pip install redistil


## Example

A basic example:

```
from redis import Redis
from redistil import Model, Field, String, Integer, Float, List

# define a model
class MyModel(Model):
    string = Field(String, primary_key=True)
    integer = Field(Integer)
    float = Field(Float)
    list = Field(List(String))


redis = Redis()

# create an object but don't save it
obj = MyModel(string='abc', integer=123, float=1.23, list=['a', 'b'])

# create an object and immediately save it
obj = MyModel.create(redis,
    string='test string',
    integer=123,
    float=4.56,
    list=['a', 'b', 'c'],
)

# load the object using the primary key field
obj = MyModel.load(redis, 'test string')

# selectively load fields
obj = MyModel.load(redis, 'test string', MyModel.integer, MyModel.float)
# primary_key will always be loaded
print(obj.string)
print(obj.integer)
print(obj.float)
# 'list' will be None

# load fields after the fact
obj.load_fields(MyModel.list)
print(obj.list)

# update and selectively save fields
obj.list = ['d', 'e', 'f']
obj.save(redis, MyModel.list)
```


## Usage

### Available Fields

Field types:

* Boolean
* Binary
* Date
* DateTime
* Float
* Integer
* Number
* String
* EmailAddress
* IPAddress
* IPV4Address
* IPV6Address
* List
* Set

Cerberus 'dict' type is not supported, instead you should flatten them into the model itself.


### Models

All data types are specified as a sub-class of Model.

Each field is specified as a class attribute which is a Field object containing a field type.

For example:

```
>>> from redistil import Model, Field, String, List
>>> from modelus.backends.memory import MemoryDatabase
>>>
>>> class MyModel(Model):
...     id = Field(String, primary_key=True)
...     values = Field(List(String), required=True)
...
>>> redis = Redis()
>>> mymodel = MyModel.create(redis, id='abc', values=['a', 'b', 'c'])
>>> # reload
>>> mymodel = MyModel.load(redis, 'abc')
>>> print(mymodel.data)
{'id': 'abc', 'values': ['a', 'b', 'c']}
```

### Field validation and defaults

Parameters to fields are simply passed through to the Cerberus schema.
[See this documentation](https://docs.python-cerberus.org/en/stable/validation-rules.html) for more Cerberus validation rules.

Selective saving of fields will only perform validation on the fields specified.

When you perform selective loading of fields, those fields' values are not loaded and may fail validation. In this case you should also perform selective saving of those same fields.

Cerberus validator rules can be added by adding a child class called "Validator" to your model definition.

```
from redistil import Model, Field, String

class MyModel(Model):
    # default_setter is a cerberus attribute which will set the value if it is not already
    # but only on save
    # the value may be either a function or a string
    # if the value is a string, the function must be defined in the Validator class as _normalize_default_setter_<name>
    # https://docs.python-cerberus.org/en/stable/normalization-rules.html
    value = Field(String, default_setter='generated_string')

    class Validator(Model.Validator):
        def _normalize_default_setter_generated_string(self, document):
            return 'abcdefg'
```

### Adding new Field Types

New field types should be as simple as sub-classing FieldType.

A type *must* define the following attributes:
* schema - Cerberus schema for the specified type

A type *may* define the following attributes:
* types_mapping - A Cerberus dictionary which is automatically added to the Cerberus.Validator.types_mapping.
* save - A function which stores the field, with signature save(db, key, field, value)
* load - A function which loads the field, with signature load(db, key, field)
* to_db - A function which converts the value to a Redis safe representation, with signature to_db(value)
* from_db - A function which converts the value to a Python representation, with signature from_db(value)

```
# Example of IPAddress which is either IPv4Address or IPv6Address
class IPAddress(FieldType):
    schema = {'type': 'ipaddress'}
    types_mapping = {'ipaddress': TypeDefinition('ipaddress', (IPv4Address, IPv6Address), ())}
    to_db = lambda self, value: str(value)
    from_db = lambda self, value: ip_address(value.decode('utf-8'))

# Example of a more complex field, which saves a list of values into a different Redis key
class List(ContainerType):
    schema = {'type': 'list'}
    save = lambda self, db, key, field, value: replace_list(db, f'{key}::{field}', value)
    load = lambda self, db, key, field: db.lrange(f'{key}::{field}', 0, -1)

    def __set_name__(self, owner, name):
        self.type.__set_name__(owner, name)

    def set(self, instance, value):
        return [self.type.set(instance, item) for item in value]

    def get(self, instance, value):
        return [self.type.get(instance, item) for item in value]
```


## Limitations

* Containers cannot be nested. Ie. lists and sets cannot contain lists, sets, or dicts.


## Future Work

* Support partial text search
* Support indexing of fields
* Improve README
