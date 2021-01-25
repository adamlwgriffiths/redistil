## Changelog

### 1.1.1

* Fix Field.key taking a key as an argument.

### 1.1.0

* Change how Field/Set/List work:
  * Field now inherits from FieldBase.
  * Set/List are now siblings of Field rather than Types.
* Rename FieldType to Type as they are not limited to Fields.
* Permit discovery of redis value paths:
  * Add key to Container types.
  * Add field to Field types.

### 1.0.0

* Initial release
