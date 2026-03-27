#!/usr/bin/env python3
"""
Minimal  Detached RO-Crate 1.2 Structure Validator

Scope:

* JUST the version 1.2 of the RO-Crate specification, and not later versions.
* JUST detached RO-Crates, not attached ones.

SPEC says:

> A Detached RO-Crate Package is an RO-Crate, defined in an RO-Crate Metadata Document without a defined root directory,
  where the RO-Crate Metadata Document content is accessed independently (e.g. as part of a programmatic API).

  Unlike an Attached RO-Crate Package, a Detached RO-Crate Package is not processed in a file-system context and thus
  does not carry a data payload in the same sense, but may reference data deposited separately, or purely reference
  contextual entities.

Copyright (c) 2026 German Bioimaging
Assisted by Claude Code
"""

import json
import sys
from pathlib import Path
from unittest import result
from urllib.parse import urlparse


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-ro-crate-metadata.json>")
        sys.exit(1)

    file_path = sys.argv[1]
    result = validate_rocrate(file_path)
    print(result)
    sys.exit(0 if result.is_valid else 1)


class ValidationResult:
    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []
        self.oks: list[str] = []

    def add_error(self, message: str):
        self.errors.append(message)

    def add_warning(self, message: str):
        self.warnings.append(message)

    def add_info(self, message: str):
        self.infos.append(message)

    def add_ok(self, message: str):
        self.oks.append(message)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def __str__(self) -> str:
        if self.is_valid:
            return "not detected as invalid - "
        return "invalid:\n  - " + "\n  - ".join(self.errors)


# TODO: Add support for absolute URIs.


def validate_rocrate(file_path: str) -> ValidationResult:
    """Validate minimal detached RO-Crate 1.2 structure."""
    result = ValidationResult()

    # Check file exists
    # SPEC says:
    # > Typically, software processing a Detached RO-Crate Package would be passed a path to a file,
    #   an absolute URI, or a JSON string or object, without a directory context.
    path = Path(file_path)
    if not path.exists():
        result.add_error(f"File not found: {file_path}")
        return result

    # Check if name is {something}-ro-crate-metadata.json
    # SPEC says:
    # > If stored in a file, known as a Detached RO-Crate Metadata File,
    #   the filename SHOULD be ${prefix}-ro-crate-metadata.json rather than ro-crate-metadata.json
    #   where the variable ${prefix} is a human readable version of the dataset’s ID or name,
    #   to signal that on disk, the presence of the file does not indicate an Attached RO-Crate Data Package.
    if not path.name.endswith("-ro-crate-metadata.json"):
        result.add_warning(
            "File name SHOULD be in the format '{prefix}-ro-crate-metadata.json' (e.g. 'idr0001-ro-crate-metadata.json')"
        )
        return result
    else:
        result.add_ok(
            "File name follows the recommended format '{prefix}-ro-crate-metadata.json'"
        )

    # Check valid JSON-LD
    # SPEC says:
    # > The RO-Crate Metadata Document MUST be a document which is valid JSON-LD 1.0 in flattened and compacted form.
    # TODO: Implement the checks for the particular JSON-LD version, and the flattened/compacted form if needed, but for now we just check if it's valid JSON.
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON: {e}")
        return result
    except Exception as e:
        result.add_error(f"Could not read file: {e}")
        return result

    # Check if it's a dict (JSON object)
    if not isinstance(data, dict):
        result.add_error("Root must be a JSON object")
        return result

    # Check @context exists and includes RO-Crate context
    # SPEC says:
    # > The RO-Crate JSON-LD MUST use the RO-Crate JSON-LD Context https://w3id.org/ro/crate/1.2/context by reference.
    context = data.get("@context")
    if context is None:
        result.add_error("Missing @context")
        return result

    context_urls = get_context_urls(context)

    # Considering valid only 1.2
    rocrate_contexts = [
        url for url in context_urls if url == "https://w3id.org/ro/crate/1.2/context"
    ]
    if not rocrate_contexts:
        result.add_error(
            "RO-Crate context not found in @context (expected 'https://w3id.org/ro/crate/1.2/context')"
        )
        return result

    # Check @graph exists and is a list
    # SPEC says:
    # > The graph MUST describe:
    #   The RO-Crate Metadata Descriptor
    #   The Root Data Entity
    #   Zero or more Data Entities
    #   Zero or more Contextual Entities

    graph = data.get("@graph")
    if graph is None:
        result.add_error("Missing @graph")
        return result
    if not isinstance(graph, list):
        result.add_error("@graph must be a JSON array")
        return result

    # Build index of entities by @id
    entities_by_id: dict[str, dict] = {}
    for entity in graph:
        if isinstance(entity, dict) and "@id" in entity:
            entities_by_id[entity["@id"]] = entity

    # Validate RO-Crate Metadata Descriptor
    # SPEC says (Root Data Entity section):
    # > The RO-Crate Metadata Document MUST contain a self-describing RO-Crate Metadata Descriptor with the @id value ro-crate-metadata.json
    #   and @type CreativeWork. This descriptor MUST have an about property referencing the Root Data Entity’s @id.
    # and
    # >  Note: Even in Detached RO-Crate Packages, where the RO-Crate Metadata File may be absent
    #   or named with a prefix, the identifier ro-crate-metadata.json MUST be used within the RO-Crate JSON-LD.

    descriptor = entities_by_id.get("ro-crate-metadata.json")
    if descriptor is None:
        result.add_error(
            "Missing RO-Crate Metadata Descriptor (entity with @id 'ro-crate-metadata.json'). Note that even if the file is named {id}-ro-crate-metadata.json,"
            "the @id inside must be 'ro-crate-metadata.json'."
        )
        return result

    if not has_type(descriptor, "CreativeWork"):
        result.add_error("Metadata Descriptor MUST have @type 'CreativeWork'")

    # Check conformsTo
    # SPEC says:
    # > The conformsTo of the RO-Crate Metadata Descriptor SHOULD have a single value which is a
    #   versioned permalink URI of the RO-Crate specification that the RO-Crate JSON-LD conforms to.
    #   The URI SHOULD start with https://w3id.org/ro/crate/.
    # NOTE: Unclear to me whether it MUST have a "conformsTo" property
    # NOTE: Even though this is the 1.2 spec,it is explicitly not requiring that the conformsTo reference 1.2

    conforms_to = descriptor.get("conformsTo")
    if conforms_to is None:
        result.add_warning("Metadata Descriptor missing 'conformsTo' property")
    else:
        conforms_to_id = get_id(conforms_to)
        if conforms_to_id is None:
            result.add_warning("Metadata Descriptor 'conformsTo' should be a reference")
        elif not conforms_to_id.startswith("https://w3id.org/ro/crate/"):
            result.add_warning(
                "Metadata Descriptor 'conformsTo' SHOULD reference RO-Crate specification"
            )

    # Check about (link to Root Data Entity)
    about = descriptor.get("about")
    if about is None:
        result.add_error("Metadata Descriptor missing 'about' property")
        return result

    root_id = get_id(about)
    if root_id is None:
        result.add_error(
            "Metadata Descriptor 'about' must reference Root Data Entity @id"
        )
        return result

    # SPEC says:
    # > In a Detached RO-Crate Package the root data entity SHOULD have an @id which is an absolute URL if it is available online.
    #   If it is not yet, or will never be available online then @id MAY be any valid URI - including ./.
    # NOTE: This ends up including the `ro-crate-metadata.json` @id as valid, perhaps a bug in the spec.
    # NOTE: The spec is actually referring to URI-reference (see https://datatracker.ietf.org/doc/html/rfc3986) which is either a URI or a relative reference.

    parsed = urlparse(root_id)
    is_uri_reference = parsed.scheme or parsed.netloc or parsed.path

    if not is_uri_reference:
        result.add_error("Root Data Entity @id MUST be a valid URI-reference")

    if not (root_id.startswith("http://") or root_id.startswith("https://")):
        result.add_warning("Root Data Entity @id SHOULD be an absolute URL")

    # Find and validate Root Data Entity
    root_entity = entities_by_id.get(root_id)
    if root_entity is None:
        result.add_error(
            f"Root Data Entity not found (expected entity with @id '{root_id}')"
        )
        return result

    if not has_type(root_entity, "Dataset"):
        result.add_error("Root Data Entity must have @type 'Dataset'")

    if "name" not in root_entity:
        result.add_error("Root Data Entity missing 'name' property")

    return result


###### Helper functions ######


def get_context_urls(context) -> set[str]:
    """Extract all URL strings from a @context (handles string, list, or dict)."""
    urls = set()
    if isinstance(context, str):
        urls.add(context)
    elif isinstance(context, list):
        for item in context:
            if isinstance(item, str):
                urls.add(item)
            # TODO: handle dict contexts with @id or nested contexts if needed
    return urls


def get_id(obj) -> str | None:
    """Extract @id from an object or reference."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return obj.get("@id")
    return None


def has_type(entity: dict, type_name: str) -> bool:
    """Check if entity has a specific @type (handles string or list)."""
    entity_type = entity.get("@type")
    if isinstance(entity_type, str):
        return entity_type == type_name
    if isinstance(entity_type, list):
        return type_name in entity_type
    return False


if __name__ == "__main__":
    main()


# TODO Parts of the specification that are not implemented at all.

# > References to files and directories in the RO-Crate Metadata Document are all Web-based Data Entities.

# > Any referenced contextual entities SHOULD also be described in the RO-Crate Metadata Document with the same identifier. Similarly any contextual entity in the RO-Crate Metadata Document SHOULD be linked to from at least one of the other entities using the same identifier.

# > Any data entities in a Detached RO-Crate Package Package MUST be Web-based Data Entities.

# > A Detached RO-Crate Package may still use #-based local identifiers for contextual entities.
