from typing import cast, List, Union

from pytest import raises

from graphql.error import GraphQLError
from graphql.language import (
    parse,
    Node,
    OperationDefinitionNode,
    ObjectTypeDefinitionNode,
    Source,
)

from ..utils import dedent


source = Source(
    dedent(
        """
        {
          field
        }
        """
    )
)

ast = parse(source)
operation_node = ast.definitions[0]
operation_node = cast(OperationDefinitionNode, operation_node)
assert operation_node and operation_node.kind == "operation_definition"
field_node = operation_node.selection_set.selections[0]
assert field_node


def describe_graphql_error():
    def is_a_class_and_is_a_subclass_of_exception():
        assert type(GraphQLError) is type
        assert issubclass(GraphQLError, Exception)
        assert isinstance(GraphQLError("str"), Exception)
        assert isinstance(GraphQLError("str"), GraphQLError)

    def has_a_name_message_and_stack_trace():
        e = GraphQLError("msg")
        assert e.__class__.__name__ == "GraphQLError"
        assert e.message == "msg"

    def uses_the_stack_of_an_original_error():
        try:
            raise RuntimeError("original")
        except RuntimeError as runtime_error:
            original = runtime_error
        e = GraphQLError("msg", original_error=original)
        assert e.__class__.__name__ == "GraphQLError"
        assert e.__traceback__ is original.__traceback__
        assert e.message == "msg"
        assert e.original_error is original
        assert str(e.original_error) == "original"

    def passes_the_context_of_an_original_error():
        context = ValueError("cause")
        try:
            raise context
        except ValueError:
            try:
                raise RuntimeError("effect")
            except RuntimeError as runtime_error:
                original = runtime_error
        e = GraphQLError("msg", original_error=original)
        assert e.__context__ is context

    def passes_the_cause_of_an_original_error():
        cause = ValueError("cause")
        try:
            raise RuntimeError("effect") from cause
        except RuntimeError as runtime_error:
            original = runtime_error
        e = GraphQLError("msg", original_error=original)
        assert e.__cause__ is cause

    def creates_new_stack_if_original_error_has_no_stack():
        try:
            raise RuntimeError
        except RuntimeError as original_with_traceback:
            original_traceback = original_with_traceback.__traceback__
            original = RuntimeError("original")
            e = GraphQLError("msg", original_error=original)
        assert e.__class__.__name__ == "GraphQLError"
        assert original.__traceback__ is None
        assert original_traceback is not None
        assert e.__traceback__ is original_traceback
        assert e.message == "msg"
        assert e.original_error is original
        assert str(e.original_error) == "original"

    def converts_nodes_to_positions_and_locations():
        e = GraphQLError("msg", [field_node])
        assert e.nodes == [field_node]
        assert e.source is source
        assert e.positions == [4]
        assert e.locations == [(2, 3)]

    def converts_single_node_to_positions_and_locations():
        e = GraphQLError("msg", field_node)  # Non-array value.
        assert e.nodes == [field_node]
        assert e.source is source
        assert e.positions == [4]
        assert e.locations == [(2, 3)]

    def converts_node_with_loc_start_zero_to_positions_and_locations():
        e = GraphQLError("msg", operation_node)
        assert e.nodes == [operation_node]
        assert e.source is source
        assert e.positions == [0]
        assert e.locations == [(1, 1)]

    def converts_source_and_positions_to_locations():
        e = GraphQLError("msg", None, source, [6])
        assert e.nodes is None
        assert e.source is source
        assert e.positions == [6]
        assert e.locations == [(2, 5)]

    def serializes_to_include_message():
        e = GraphQLError("msg")
        assert str(e) == "msg"
        assert repr(e) == "GraphQLError('msg')"

    def serializes_to_include_message_and_locations():
        e = GraphQLError("msg", field_node)
        assert "msg" in str(e)
        assert ":2:3" in str(e)
        assert repr(e) == (
            "GraphQLError('msg', locations=[SourceLocation(line=2, column=3)])"
        )
        assert e.formatted == {
            "locations": [{"column": 3, "line": 2}],
            "message": "msg",
        }

    def repr_includes_extensions():
        e = GraphQLError("msg", extensions={"foo": "bar"})
        assert repr(e) == "GraphQLError('msg', extensions={'foo': 'bar'})"

    def serializes_to_include_path():
        path: List[Union[int, str]] = ["path", 3, "to", "field"]
        e = GraphQLError("msg", path=path)
        assert e.path is path
        assert repr(e) == "GraphQLError('msg', path=['path', 3, 'to', 'field'])"
        assert e.formatted == {
            "message": "msg",
            "path": ["path", 3, "to", "field"],
        }

    def always_stores_path_as_list():
        path: List[Union[int, str]] = ["path", 3, "to", "field"]
        e = GraphQLError("msg,", path=tuple(path))
        assert isinstance(e.path, list)
        assert e.path == path

    def is_comparable():
        e1 = GraphQLError("msg,", path=["field", 1])
        assert e1 == e1
        assert e1 == e1.formatted
        assert not e1 != e1
        assert not e1 != e1.formatted
        e2 = GraphQLError("msg,", path=["field", 1])
        assert e1 == e2
        assert not e1 != e2
        assert e2.path and e2.path[1] == 1
        e2.path[1] = 2
        assert not e1 == e2
        assert e1 != e2
        assert not e1 == e2.formatted
        assert e1 != e2.formatted

    def is_hashable():
        hash(GraphQLError("msg"))

    def hashes_are_unique_per_instance():
        e1 = GraphQLError("msg")
        e2 = GraphQLError("msg")
        assert hash(e1) != hash(e2)


def describe_to_string():
    def deprecated_prints_an_error_using_print_error():
        # noinspection PyProtectedMember
        from graphql.error.graphql_error import print_error

        error = GraphQLError("Error")
        assert print_error(error) == "Error"
        with raises(TypeError) as exc_info:
            # noinspection PyTypeChecker
            print_error(Exception)  # type: ignore
        assert str(exc_info.value) == "Expected a GraphQLError."

    def prints_an_error_without_location():
        error = GraphQLError("Error without location")
        assert str(error) == "Error without location"

    def prints_an_error_using_node_without_location():
        error = GraphQLError(
            "Error attached to node without location",
            parse("{ foo }", no_location=True),
        )
        assert str(error) == "Error attached to node without location"

    def prints_an_error_with_nodes_from_different_sources():
        doc_a = parse(
            Source(
                dedent(
                    """
                    type Foo {
                      field: String
                    }
                    """
                ),
                "SourceA",
            )
        )
        op_a = doc_a.definitions[0]
        op_a = cast(ObjectTypeDefinitionNode, op_a)
        assert op_a and op_a.kind == "object_type_definition" and op_a.fields
        field_a = op_a.fields[0]
        doc_b = parse(
            Source(
                dedent(
                    """
                    type Foo {
                      field: Int
                    }
                    """
                ),
                "SourceB",
            )
        )
        op_b = doc_b.definitions[0]
        op_b = cast(ObjectTypeDefinitionNode, op_b)
        assert op_b and op_b.kind == "object_type_definition" and op_b.fields
        field_b = op_b.fields[0]

        error = GraphQLError(
            "Example error with two nodes", [field_a.type, field_b.type]
        )

        assert str(error) == dedent(
            """
            Example error with two nodes

            SourceA:2:10
            1 | type Foo {
            2 |   field: String
              |          ^
            3 | }

            SourceB:2:10
            1 | type Foo {
            2 |   field: Int
              |          ^
            3 | }
            """
        )


def describe_formatted():
    def deprecated_formats_an_error_using_format_error():
        # noinspection PyProtectedMember
        from graphql.error.graphql_error import format_error

        error = GraphQLError("Example Error")
        assert format_error(error) == {
            "message": "Example Error",
        }
        with raises(TypeError) as exc_info:
            # noinspection PyTypeChecker
            format_error(Exception)  # type: ignore
        assert str(exc_info.value) == "Expected a GraphQLError."

    def formats_graphql_error():
        path: List[Union[int, str]] = ["one", 2]
        extensions = {"ext": None}
        error = GraphQLError(
            "test message",
            Node(),
            Source(
                """
                query {
                  something
                }
                """
            ),
            [16, 41],
            ["one", 2],
            ValueError("original"),
            extensions=extensions,
        )
        assert error.formatted == {
            "message": "test message",
            "locations": [{"line": 2, "column": 16}, {"line": 3, "column": 17}],
            "path": path,
            "extensions": extensions,
        }

    def uses_default_message():
        # noinspection PyTypeChecker
        formatted = GraphQLError(None).formatted  # type: ignore

        assert formatted == {
            "message": "An unknown error occurred.",
        }

    def includes_path():
        path: List[Union[int, str]] = ["path", 3, "to", "field"]
        error = GraphQLError("msg", path=path)
        assert error.formatted == {"message": "msg", "path": path}

    def includes_extension_fields():
        error = GraphQLError("msg", extensions={"foo": "bar"})
        assert error.formatted == {
            "message": "msg",
            "extensions": {"foo": "bar"},
        }
