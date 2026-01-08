import re

import bleach

from django.core.exceptions import ValidationError
from django.template import Engine, TemplateSyntaxError
from django.template.base import VariableNode


INVALID = "__INVALID__%s__"


def extract_vars(template):
    """Extract all variable names from Django template AST."""
    used = set()

    def walk(nodelist):
        for node in nodelist:
            # {{ var }}
            if isinstance(node, VariableNode):
                used.add(node.filter_expression.token.split("|")[0].split(".")[0].strip())

            # {% if var %}, {% for x in var %}, {% with var as x %}
            for attr in ("var", "sequence", "value", "filter_expression"):
                expr = getattr(node, attr, None)
                if expr and hasattr(expr, "token"):
                    used.add(expr.token.split("|")[0].split(".")[0].strip())

            for child in ("nodelist", "nodelist_true", "nodelist_false", "nodelist_loop"):
                if hasattr(node, child):
                    walk(getattr(node, child))

    walk(template.nodelist)
    return {v for v in used if v and not v.isdigit() and v[0] not in "\"'"}


def validate_template(html: str, channel, allowed_vars: list[str], is_custom=False):
    """
    Validate notification template
    """
    allowed_vars = allowed_vars or []
    
    # template syntax check
    try:
        engine = Engine(debug=True, string_if_invalid=INVALID)
        tpl = engine.from_string(html)
    except TemplateSyntaxError as e:
        raise ValidationError({"html": f"Template syntax error: {e}"})

    # variables extraction
    used = extract_vars(tpl)
    
    # variables validation
    if is_custom:
        if used:
            raise ValidationError({
                "html": f"Variables are not allowed for custom types. Found: {', '.join(sorted(used))}"
            })
    else:
        # unknown variables validation
        unknown = sorted(v for v in used if v not in set(allowed_vars))
        if unknown:
            raise ValidationError({
                "html": f"Unknown variables: {', '.join(unknown)}. Allowed: {', '.join(sorted(allowed_vars))}"
            })
        
        # required variables validation
        missing = sorted(v for v in allowed_vars if v not in used)
        if missing:
            raise ValidationError({
                "html": f"Missing required variables: {', '.join(missing)} Required: {', '.join(sorted(allowed_vars))}"
            })

    # allowed tags validation
    allowed = [t.lower() for t in (channel.allowed_tags or [])]
    cleaned = bleach.clean(html, tags=allowed, strip=True)

    if cleaned != html:
        raise ValidationError({"html": "Template contains forbidden HTML tags"})


def validate_template_uniqueness(template_instance):
    """
    Validate template uniqueness based on type
    """
    if template_instance.notification_type.is_custom:
        qs = template_instance.__class__.objects.filter(
            notification_type=template_instance.notification_type,
            channel=template_instance.channel,
            name=template_instance.name
        )
        field = 'name'
    else:
        qs = template_instance.__class__.objects.filter(
            notification_type=template_instance.notification_type,
            channel=template_instance.channel
        )
        field = 'channel'
    
    if template_instance.pk:
        qs = qs.exclude(pk=template_instance.pk)
    
    if qs.exists():
        name = template_instance.name if template_instance.notification_type.is_custom else template_instance.notification_type.title
        raise ValidationError({
            field: f'Template "{name}" for type "{template_instance.notification_type.title}" and channel "{template_instance.channel.title}" already exists'
        })
