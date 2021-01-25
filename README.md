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
    list = List(String)


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

# determine where values are saved so we can bypass the object model if we want to
MyModel.key('test string')
# 'MyModel::test string'
MyModel.string.field()
# 'string'
MyModel.list.key(MyModel.key('test string'))
# 'MyModel::test string::list'
```


## Usage

### Available Fields

Properties:

* Field - Indicates a Redish hash field
* Set - A set associated with the model
* List - A list associated with the model

Cerberus 'dict' type is not supported, instead you should flatten them into the model itself.

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



### Models

All data types are specified as a sub-class of Model.

Each field is specified as a class attribute which is a Field object containing a field type.

For example:

```
>>> from redis import Redis
>>> from redistil import Model, Field, String, List
>>>
>>> class MyModel(Model):
...     id = Field(String, primary_key=True)
...     values = List(String, required=True)
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


## Limitations

* Containers cannot be nested. Ie. lists and sets cannot contain lists, sets, or dicts.


## Future Work

* Support partial text search
* Support indexing of fields
* Improve README
