# -*- coding: utf-8 -*-

import json

from flask import make_response
from marshmallow import fields, Schema

from flask_apispec.utils import Ref, match_status_code
from flask_apispec.views import MethodResource
from flask_apispec import doc, use_kwargs, marshal_with

class TestFunctionViews:

    def test_use_kwargs(self, app, client):
        @app.route('/')
        @use_kwargs({'name': fields.Str()})
        def view(**kwargs):
            return kwargs
        res = client.get('/', {'name': 'freddie'})
        assert res.json == {'name': 'freddie'}

    def test_use_kwargs_schema(self, app, client):
        class ArgSchema(Schema):
            name = fields.Str()

            class Meta:
                strict = True

        @app.route('/')
        @use_kwargs(ArgSchema)
        def view(**kwargs):
            return kwargs
        res = client.get('/', {'name': 'freddie'})
        assert res.json == {'name': 'freddie'}

    def test_use_kwargs_schema_many(self, app, client):
        class ArgSchema(Schema):
            name = fields.Str()

        @app.route('/', methods=('POST',))
        @use_kwargs(ArgSchema(many=True), locations=('json',))
        def view(*args):
            return list(args)
        data = [{'name': 'freddie'}, {'name': 'john'}]
        res = client.post('/', json.dumps(data), content_type='application/json')
        assert res.json == data

    def test_use_kwargs_multiple(self, app, client):
        @app.route('/')
        @use_kwargs({'name': fields.Str()})
        @use_kwargs({'instrument': fields.Str()})
        def view(**kwargs):
            return kwargs
        res = client.get('/', {'name': 'freddie', 'instrument': 'vocals'})
        assert res.json == {'name': 'freddie', 'instrument': 'vocals'}

    def test_marshal_with_default(self, app, client, models, schemas):
        @app.route('/')
        @marshal_with(schemas.BandSchema)
        def view():
            return models.Band('queen', 'rock')
        res = client.get('/')
        assert res.json == {'name': 'queen', 'genre': 'rock'}

    def test_marshal_with_codes(self, app, client, models, schemas):
        @app.route('/')
        @marshal_with(schemas.BandSchema)
        @marshal_with(schemas.BandSchema(only=('name', )), code=201)
        def view():
            return models.Band('queen', 'rock'), 201
        res = client.get('/')
        assert res.json == {'name': 'queen'}

    def test_marshal_with_apply(self, app, client, models, schemas):
        @app.route('/')
        @marshal_with(schemas.BandSchema, apply=lambda req, res: res.status_code == 200)
        @marshal_with(schemas.BandSchema(only=('name',)), apply=lambda req, res: res.status_code == 201)
        def view():
            return models.Band('queen', 'rock'), 201
        res = client.get('/')
        assert res.json == {'name': 'queen'}

    def test_marshal_with_apply_alternative(self, app, client, models, schemas):
        @app.route('/')
        @marshal_with(schemas.BandSchema(only=('genre',)), apply=lambda req, res: res.status_code == 200)
        @marshal_with(schemas.BandSchema(only=('name',)), apply=lambda req, res: res.status_code == 201)
        def view():
            return models.Band('queen', 'rock'), 200
        res = client.get('/')
        assert res.json == {'genre': 'rock'}

    def test_marshal_with_apply_default(self, app, client, models, schemas):
        @app.route('/')
        @marshal_with(schemas.BandSchema(only=('genre', )), apply=lambda req, res: res.status_code == 200)
        @marshal_with(schemas.BandSchema(only=('name', )), apply=lambda req, res: res.status_code == 201)
        def view():
            return models.Band('queen', 'rock')
        res = client.get('/')
        assert res.json == {'genre': 'rock'}

    def test_marshal_with_apply_via_headers(self, app, client, models, schemas):
        import re
        pattern = r'application/vnd\.(?P<vendor_id>\w+)(\.(\w+))*\.v(?P<version_number>\d+)(\+\w+)?'
        compiled = re.compile(pattern)
        def _get_version(mimetype):
            m = compiled.match(mimetype)
            if m and m.group("version_number"):
                return int(m.group("version_number"))
        def is_v5(req):
            for mt in req.accept_mimetypes.values():
                v = _get_version(mt)
                if v == 5:
                    return True
            return False

        @app.route('/')
        @marshal_with(schemas.BandSchema, code = 200, apply=lambda req, res: is_v5(req))
        @marshal_with(schemas.BandSchema(only=('name',)), code = 200, apply=lambda req, res: res.status_code == 200)
        def view():
            return models.Band('queen', 'rock')
        res = client.get('/', headers = {'Accept': 'application/vnd.company.v5'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

    def test_marshal_with_apply_via_headers_fallthru(self, app, client, models, schemas):
        def is_v5(req):
            return False
        @app.route('/')
        @marshal_with(schemas.BandSchema, code = 200, apply=lambda req, res: is_v5(req))
        @marshal_with(schemas.BandSchema(only=('name',)), code = 200, apply=lambda req, res: res.status_code == 200)
        def view():
            return models.Band('queen', 'rock')
        res = client.get('/')
        assert res.json == {'name': 'queen'}

    def test_marshal_with_apply_via_headers_fallthru_2(self, app, client, models, schemas):
        def is_v5(req):
            return False
        @app.route('/')
        @marshal_with(schemas.BandSchema, code = 200, apply=lambda req, res: is_v5(req))
        @marshal_with(schemas.BandSchema(only=('name',)), code = 200, apply=match_status_code(200))
        def view():
            return models.Band('queen', 'rock')
        res = client.get('/')
        assert res.json == {'name': 'queen'}

    def test_marshal_with_apply_via_headers_fallthru_3(self, app, client, models, schemas):
        def is_v5(req):
            return False
        @app.route('/')
        @marshal_with(schemas.BandSchema(only=('name',)), code = 200)
        @marshal_with(schemas.BandSchema, code = 200, apply=lambda req, res: is_v5(req))
        def view():
            return models.Band('queen', 'rock')
        res = client.get('/')
        assert res.json == {'name': 'queen'}

    def test_marshal_with_apply_via_headers_fallthru_4(self, app, client, models, schemas):
        def is_v5(req):
            return False
        @app.route('/')
        @marshal_with(schemas.BandSchema(only=('name',)), code = 200)
        @marshal_with(schemas.BandSchema, code = 200, apply=lambda req, res: is_v5(req))
        def view():
            return models.Band('queen', 'rock')
        res = client.get('/')
        assert res.json == {'name': 'queen'}

    def test_marshal_with_apply_via_headers_fallthru_5(self, app, client, models, schemas):
        def is_v5(req):
            return False
        @app.route('/')
        @marshal_with(schemas.BandSchema(only=('name',)))
        @marshal_with(schemas.BandSchema, code = 200, apply=lambda req, res: is_v5(req))
        def view():
            return models.Band('queen', 'rock')
        res = client.get('/')
        assert res.json == {'name': 'queen'}

    def test_marshal_with_apply_via_headers_fallthru_6(self, app, client, models, schemas):
        def is_v5(req):
            return False
        @app.route('/')
        @marshal_with(schemas.BandSchema(only=('genre',)), code = 201)
        @marshal_with(schemas.BandSchema(only=('name',)), code = 200)
        @marshal_with(schemas.BandSchema, apply=lambda req, res: is_v5(req))
        def view():
            return models.Band('queen', 'rock'), 201
        res = client.get('/')
        assert res.json == {'genre': 'rock'}

    def test_integration(self, app, client, models, schemas):
        @app.route('/')
        @use_kwargs({'name': fields.Str(), 'genre': fields.Str()})
        @marshal_with(schemas.BandSchema)
        def view(**kwargs):
            return models.Band(**kwargs)
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

class TestClassViews:

    def test_inheritance_unidirectional(self, app, client):
        @doc(tags=['base'])
        class BaseResource(MethodResource):
            @doc(description='parent')
            def get(self, **kwargs):
                pass

        @doc(tags=['child'])
        class ChildResource(BaseResource):
            @doc(description='child')
            def get(self, **kwargs):
                return kwargs

        assert not any(MethodResource.__apispec__.values())

        assert BaseResource.__apispec__['docs'][0].options[0]['tags'] == ['base']
        assert ChildResource.__apispec__['docs'][0].options[0]['tags'] == ['child']

        assert BaseResource.get.__apispec__['docs'][0].options[0]['description'] == 'parent'
        assert ChildResource.get.__apispec__['docs'][0].options[0]['description'] == 'child'

    def test_inheritance_only_http_methods(self, app):
        @use_kwargs({'genre': fields.Str()})
        class ConcreteResource(MethodResource):
            def _helper(self, **kwargs):
                return kwargs

        with app.test_request_context():
            resource = ConcreteResource()
            assert resource._helper() == {}

    def test_kwargs_inheritance(self, app, client):
        class BaseResource(MethodResource):
            @use_kwargs({'name': fields.Str()})
            def get(self, **kwargs):
                pass

        class ConcreteResource(BaseResource):
            @use_kwargs({'genre': fields.Str()})
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

    def test_kwargs_inheritance_ref(self, app, client, schemas):
        class BaseResource(MethodResource):
            @use_kwargs({'name': fields.Str()})
            def get(self, **kwargs):
                pass

        class ConcreteResource(BaseResource):
            kwargs = {'genre': fields.Str()}
            @use_kwargs(Ref('kwargs'))
            @marshal_with(schemas.BandSchema)
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen', 'genre': 'rock'}

    def test_kwargs_inheritance_false(self, app, client, models, schemas):
        class BaseResource(MethodResource):
            @use_kwargs({'name': fields.Str(), 'genre': fields.Str()})
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            @use_kwargs({'name': fields.Str()}, inherit=False)
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {'name': 'queen'}

    def test_kwargs_apply_false(self, app, client):
        class ConcreteResource(MethodResource):
            @use_kwargs({'genre': fields.Str()}, apply=False)
            def get(self, **kwargs):
                return kwargs

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/', {'name': 'queen', 'genre': 'rock'})
        assert res.json == {}

    def test_schemas_class(self, app, client, models, schemas):
        @marshal_with(schemas.BandSchema)
        class ConcreteResource(MethodResource):
            @marshal_with(schemas.BandSchema(only=('genre', )), code=201)
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze'), 201

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'shoegaze'}

    def test_schemas_class_inheritance(self, app, client, models, schemas):
        @marshal_with(schemas.BandSchema(only=('genre', )))
        class BaseResource(MethodResource):
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze'), 201

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'shoegaze'}

    def test_schemas_inheritance(self, app, client, models, schemas):
        class BaseResource(MethodResource):
            @marshal_with(schemas.BandSchema)
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            @marshal_with(schemas.BandSchema(only=('genre', )), code=201)
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze'), 201

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'shoegaze'}

    def test_schemas_inheritance_refs(self, app, client, models, schemas):
        class BaseResource(MethodResource):
            schema = None

            @marshal_with(Ref('schema'))
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            schema = schemas.BandSchema

            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze')

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'name': 'slowdive', 'genre': 'shoegaze'}

    def test_schemas_inheritance_false(self, app, client, models, schemas):
        class BaseResource(MethodResource):
            @marshal_with(schemas.BandSchema, code=201)
            def get(self):
                pass

        class ConcreteResource(BaseResource):
            @marshal_with(schemas.BandSchema(only=('genre', )), inherit=False)
            def get(self, **kwargs):
                return models.Band('slowdive', 'shoegaze'), 201

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'shoegaze'}

    def test_schemas_apply_false(self, app, client, models, schemas):
        class ConcreteResource(MethodResource):
            @marshal_with(schemas.BandSchema, apply=False)
            def get(self, **kwargs):
                return {'genre': 'spacerock'}

        app.add_url_rule('/', view_func=ConcreteResource.as_view('concrete'))
        res = client.get('/')
        assert res.json == {'genre': 'spacerock'}

    def test_schemas_none(self, app, client, models, schemas):
        class ConcreteResource(MethodResource):
            @marshal_with(None, code=204)
            def delete(self, **kwargs):
                return make_response('', 204)

        app.add_url_rule('/<id>/', view_func=ConcreteResource.as_view('concrete'))
        res = client.delete('/5/')
        assert res.body == b''
