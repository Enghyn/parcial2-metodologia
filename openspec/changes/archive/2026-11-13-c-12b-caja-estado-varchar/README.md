# c-12b-caja-estado-varchar

Bugfix de C-12: la migracion 0008 creo un ENUM nativo de Postgres pero el modelo declara String(20); toda query que filtra por estado falla con UndefinedFunction.
