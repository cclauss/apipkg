import types
import sys
import py

#
# test support for importing modules
#

class TestRealModule:

    def setup_class(cls):
        cls.tmpdir = py.test.ensuretemp('test_apipkg')
        sys.path = [str(cls.tmpdir)] + sys.path
        pkgdir = cls.tmpdir.ensure('realtest', dir=1)

        tfile = pkgdir.join('__init__.py')
        tfile.write(py.code.Source("""
            import apipkg
            apipkg.initpkg(__name__, {
                'x': {
                    'module': {
                        '__doc__': '_xyz.testmodule:__doc__',
                        'mytest0': '_xyz.testmodule:mytest0',
                        'mytest1': '_xyz.testmodule:mytest1',
                        'MyTest':  '_xyz.testmodule:MyTest',
                    }
                }
            }
            )
        """))

        ipkgdir = cls.tmpdir.ensure("_xyz", dir=1)
        tfile = ipkgdir.join('testmodule.py')
        ipkgdir.ensure("__init__.py")
        tfile.write(py.code.Source("""
            'test module'
            from _xyz.othermodule import MyTest

            #__all__ = ['mytest0', 'mytest1', 'MyTest']

            def mytest0():
                pass
            def mytest1():
                pass
        """))
        ipkgdir.join("othermodule.py").write("class MyTest: pass")

    def setup_method(self, *args):
        # Unload the test modules before each test.
        module_names = ['realtest', 'realtest.x', 'realtest.x.module']
        for modname in module_names:
            if modname in sys.modules:
                del sys.modules[modname]

    def test_realmodule(self):
        import realtest.x
        assert 'realtest.x.module' in sys.modules
        assert getattr(realtest.x.module, 'mytest0')

    def test_realmodule_repr(self):
        import realtest.x
        assert "<ApiModule 'realtest.x'>"  == repr(realtest.x)

    def test_realmodule_from(self):
        from realtest.x import module
        assert getattr(module, 'mytest1')

    def test_realmodule__all__(self):
        import realtest.x.module
        assert realtest.x.__all__ == ['module']
        assert len(realtest.x.module.__all__) == 4

    def test_realmodule_dict_import(self):
        "Test verifying that accessing the __dict__ invokes the import"
        import realtest.x.module
        moddict = realtest.x.module.__dict__
        assert 'mytest0' in moddict
        assert 'mytest1' in moddict
        assert 'MyTest' in moddict

    def test_realmodule___doc__(self):
        """test whether the __doc__ attribute is set properly from initpkg"""
        import realtest.x.module
        print (realtest.x.module.__map__)
        assert realtest.x.module.__doc__ == 'test module'

# alternate ideas for specifying package + preliminary code
#
def test_parsenamespace():
    spec = """
        path.local    __.path.local::LocalPath
        path.svnwc    __.path.svnwc::WCCommandPath
        test.raises   __.test.outcome::raises
    """
    d = parsenamespace(spec)
    print d
    assert d == {'test': {'raises': '__.test.outcome::raises'},
                 'path': {'svnwc': '__.path.svnwc::WCCommandPath',
                          'local': '__.path.local::LocalPath'}
            }
def xtest_parsenamespace_errors():
    py.test.raises(ValueError, """
        parsenamespace('path.local xyz')
    """)
    py.test.raises(ValueError, """
        parsenamespace('x y z')
    """)

def parsenamespace(spec):
    ns = {}
    for line in spec.split("\n"):
        line = line.strip()
        if not line or line[0] == "#":
            continue
        parts = [x.strip() for x in line.split()]
        if len(parts) != 2:
            raise ValueError("Wrong format: %r" %(line,))
        apiname, spec = parts
        if not spec.startswith("__"):
            raise ValueError("%r does not start with __" %(spec,))
        apinames = apiname.split(".")
        cur = ns
        for name in apinames[:-1]:
            cur.setdefault(name, {})
            cur = cur[name]
        cur[apinames[-1]] = spec
    return ns
