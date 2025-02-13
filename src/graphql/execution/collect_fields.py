from typing import Any, Dict, List, Set, Union, cast

from ..language import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    SelectionSetNode,
)
from ..type import (
    GraphQLAbstractType,
    GraphQLIncludeDirective,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLSkipDirective,
    is_abstract_type,
)
from ..utilities.type_from_ast import type_from_ast
from .values import get_directive_values

__all__ = ["collect_fields"]


def collect_fields(
    schema: GraphQLSchema,
    fragments: Dict[str, FragmentDefinitionNode],
    variable_values: Dict[str, Any],
    runtime_type: GraphQLObjectType,
    selection_set: SelectionSetNode,
    fields: Dict[str, List[FieldNode]],
    visited_fragment_names: Set[str],
) -> Dict[str, List[FieldNode]]:
    """Collect fields.

    Given a selection_set, adds all of the fields in that selection to the passed in
    map of fields, and returns it at the end.

    collect_fields requires the "runtime type" of an object. For a field which
    returns an Interface or Union type, the "runtime type" will be the actual
    Object type returned by that field.

    For internal use only.
    """
    for selection in selection_set.selections:
        if isinstance(selection, FieldNode):
            if not should_include_node(variable_values, selection):
                continue
            name = get_field_entry_key(selection)
            fields.setdefault(name, []).append(selection)
        elif isinstance(selection, InlineFragmentNode):
            if not should_include_node(
                variable_values, selection
            ) or not does_fragment_condition_match(schema, selection, runtime_type):
                continue
            collect_fields(
                schema,
                fragments,
                variable_values,
                runtime_type,
                selection.selection_set,
                fields,
                visited_fragment_names,
            )
        elif isinstance(selection, FragmentSpreadNode):  # pragma: no cover else
            frag_name = selection.name.value
            if frag_name in visited_fragment_names or not should_include_node(
                variable_values, selection
            ):
                continue
            visited_fragment_names.add(frag_name)
            fragment = fragments.get(frag_name)
            if not fragment or not does_fragment_condition_match(
                schema, fragment, runtime_type
            ):
                continue
            collect_fields(
                schema,
                fragments,
                variable_values,
                runtime_type,
                fragment.selection_set,
                fields,
                visited_fragment_names,
            )
    return fields


def should_include_node(
    variable_values: Dict[str, Any],
    node: Union[FragmentSpreadNode, FieldNode, InlineFragmentNode],
) -> bool:
    """Check if node should be included

    Determines if a field should be included based on the @include and @skip
    directives, where @skip has higher precedence than @include.
    """
    skip = get_directive_values(GraphQLSkipDirective, node, variable_values)
    if skip and skip["if"]:
        return False

    include = get_directive_values(GraphQLIncludeDirective, node, variable_values)
    if include and not include["if"]:
        return False

    return True


def does_fragment_condition_match(
    schema: GraphQLSchema,
    fragment: Union[FragmentDefinitionNode, InlineFragmentNode],
    type_: GraphQLObjectType,
) -> bool:
    """Determine if a fragment is applicable to the given type."""
    type_condition_node = fragment.type_condition
    if not type_condition_node:
        return True
    conditional_type = type_from_ast(schema, type_condition_node)
    if conditional_type is type_:
        return True
    if is_abstract_type(conditional_type):
        return schema.is_sub_type(cast(GraphQLAbstractType, conditional_type), type_)
    return False


def get_field_entry_key(node: FieldNode) -> str:
    """Implements the logic to compute the key of a given field's entry"""
    return node.alias.value if node.alias else node.name.value
