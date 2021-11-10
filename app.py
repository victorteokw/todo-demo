from __future__ import annotations
from datetime import datetime
from dotenv import load_dotenv
from jsonclasses import jsonclass, types
from jsonclasses_pymongo import pymongo
from jsonclasses_server import api, authorized, create_flask_server


# Load environment variables from .env file
load_dotenv()


# If you want to change the default database URL, uncomment and modify this:
#
# from jsonclasses_pymongo import Connection
# Connection.default.set_url('mongodb://localhost:27017/yourdb')


# You can create a model by using class and type hint syntax, with decorators
# decorated.
#
# Models with relationships are supported.
#
# To understand the types modifier pipeline syntax, check our documentation:
#
# https://docs.jsonclasses.com/docs/api-documentation/types-modifiers
#
# @api
# @pymongo
# @jsonclass
# class MyModel:
#     id: str = types.readonly.str.primary.mongoid.required
#     one: str
#     two: int = 1
#     created_at: datetime = types.readonly.datetime.tscreated.required
#     updated_at: datetime = types.readonly.datetime.tsupdated.required


@authorized
@api
@pymongo
@jsonclass(
    on_create=lambda user: user.opby(user),
    can_update=types.getop.isthis,
    can_delete=types.getop.isthis,
    can_read=types.getop.isthis
)
class User:
    id: str = types.readonly.str.primary.mongoid.required
    email: str = types.str.email.unique.authidentity.required
    password: str = types.writeonly.str.securepw.length(8, 16).salt.authbycheckpw.required
    name: str | None
    todo_lists: list[TodoList] = types.listof('TodoList').linkedby('owner')
    todo_entries: list[TodoEntry] = types.listof('TodoEntry').linkedby('owner')
    created_at: datetime = types.readonly.datetime.tscreated.required
    updated_at: datetime = types.readonly.datetime.tsupdated.required


@api
@pymongo
@jsonclass(
    can_create=types.getop.isobjof(User),
    can_update=types.getop.isobj(types.this.fval('owner')),
    can_delete=types.getop.isobj(types.this.fval('owner')),
    can_read=types.getop.isobj(types.this.fval('owner'))
)
class TodoList:
    id: str = types.readonly.str.primary.mongoid.required
    title: str = types.str.default('Untitled List').required
    owner: User = types.readonly.objof('User').linkto.asopd.required
    entries: list[TodoEntry] = types.listof('TodoEntry').linkedby('todo_list')
    created_at: datetime = types.readonly.datetime.tscreated.required
    updated_at: datetime = types.readonly.datetime.tsupdated.required


@api
@pymongo
@jsonclass(
    can_create=types.getop.isobj(types.this.fobj('todo_list').fval('owner')),
    can_update=types.getop.isobj(types.this.fval('owner')),
    can_delete=types.getop.isobj(types.this.fval('owner')),
    can_read=types.getop.isobj(types.this.fval('owner'))
)
class TodoEntry:
    id: str = types.readonly.str.primary.mongoid.required
    title: str = types.str.default('').required
    detail: str | None
    due_at: datetime | None
    completed_at: datetime | None
    order: int
    overdue: bool = types.bool.getter(lambda entry: False if entry.due_at is None else entry.due_at < datetime.now())
    completed: bool = types.bool.getter(lambda entry: entry.completed_at is not None)
    owner: User = types.readonly.objof('User').linkto.asopd.required
    todo_list: TodoList = types.objof('TodoList').linkto.required
    created_at: datetime = types.readonly.datetime.tscreated.required
    updated_at: datetime = types.readonly.datetime.tsupdated.required


@authorized
@api
@pymongo
@jsonclass
class Admin:
    id: str = types.readonly.str.primary.mongoid.required
    email: str = types.str.email.unique.authidentity.required
    password: str = types.writeonly.str.securepw.length(8, 16).salt.authbycheckpw.required
    name: str | None
    created_at: datetime = types.readonly.datetime.tscreated.required
    updated_at: datetime = types.readonly.datetime.tsupdated.required


app = create_flask_server()


# You can still write custom routes if synthesized routes don't satisfy your
# need. To understand the ORM methods, check our documentation:
#
# https://docs.jsonclasses.com/docs/api-documentation/orm-addons
