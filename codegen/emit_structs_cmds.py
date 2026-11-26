"""Generate src/generated/{types,commands,dispatch}.rs."""

from __future__ import annotations

from vkxml import VkRegistry, VkType, VkVariable
from emit_protocol import (
    BANNER,
    COMMAND_BLOCK_LIST,
    UNION_DEFAULT_TAGS,
    emit_scalar_decode,
    emit_scalar_encode,
    emit_struct_decode_member,
    emit_struct_encode_member,
    field_name,
    get_chain,
    is_serializable,
    rust_base_type,
    to_snake,
    var_rust_type,
)


def emit_unions(reg: VkRegistry, supported: set[VkType]) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    for name, ty in reg.type_table.items():
        if ty not in supported or ty.category != VkType.UNION or name != ty.name or name in seen:
            continue
        if not is_serializable(ty):
            continue
        seen.add(name)
        cases = ty.get_union_cases()
        valid_cases = [(tag, var) for tag, var in cases if is_serializable(var)]
        if not valid_cases:
            continue

        # Deduplicate variant names (e.g. VkResourceDescriptorDataEXT has multiple pImage)
        lines.append(f"#[derive(Clone, Debug, PartialEq)]\npub enum {name} {{\n")
        variant_names: list[tuple[str, str, VkVariable]] = []
        used_vnames: set[str] = set()
        for tag, var in valid_cases:
            vname = var.name[0].upper() + var.name[1:]
            if vname in used_vnames:
                vname = f"{vname}_{tag}"
            used_vnames.add(vname)
            rty = var_rust_type(name, var) or "u32"
            variant_names.append((str(tag), vname, var))
            lines.append(f"    {vname}({rty}),\n")
        lines.append("}\n\n")

        # Default impl using first variant
        _, first_vname, first_var = variant_names[0]
        lines.append(
            f"impl Default for {name} {{\n"
            f"    fn default() -> Self {{\n"
            f"        Self::{first_vname}(Default::default())\n"
            f"    }}\n"
            f"}}\n\n"
        )

        # decode / encode
        tag_type = ty.sty.name if ty.is_valid_union() else "u32"
        lines.append(f"impl {name} {{\n")
        lines.append("    pub fn decode(dec: &mut Decoder<'_>) -> Result<Self, WireError> {\n")
        if ty.is_valid_union():
            lines.append(f"        let tag = {tag_type}::decode(dec)?;\n")
        else:
            lines.append("        let tag = dec.read_u32()?;\n")
        lines.append("        match tag {\n")
        for tag, vname, var in variant_names:
            pat = f"{tag_type}::{tag}" if ty.is_valid_union() else tag
            lines.append(f"            {pat} => {{\n")
            dl = emit_struct_decode_member(ty, var, {}, False, "                ")
            lines.extend(dl)
            lines.append(f"                Ok(Self::{vname}({field_name(var)}))\n")
            lines.append("            }\n")
        lines.append("            _ => Err(WireError::InvalidStructureType(0)),\n")
        lines.append("        }\n    }\n\n")

        lines.append("    pub fn encode<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n")
        lines.append("        match self {\n")
        for tag, vname, var in variant_names:
            lines.append(f"            Self::{vname}(val) => {{\n")
            if ty.is_valid_union():
                lines.append(f"                {tag_type}::{tag}.encode(enc)?;\n")
            else:
                lines.append(f"                enc.write_u32({tag})?;\n")
            # Encode val using a temporary variable named after var
            fn = field_name(var)
            if var.ty.is_static_array() or var.ty.is_pointer() or var.ty.base.category in (var.ty.base.STRUCT, var.ty.base.UNION):
                lines.append(f"                let {fn} = val;\n")
            else:
                lines.append(f"                let {fn} = *val;\n")
            el = emit_struct_encode_member(ty, var, {}, False, "", "                ")
            lines.extend(el)
            lines.append("                Ok(())\n")
            lines.append("            }\n")
        lines.append("        }\n    }\n}\n\n")
    return "".join(lines)


def struct_has_large_array(ty: VkType) -> bool:
    for var in ty.variables:
        if var.ty.is_static_array() and is_serializable(var):
            dim = var.ty.decor.dim
            if dim != "3][4":
                return True  # constants or >32
    return False


def emit_structs(reg: VkRegistry, supported: set[VkType]) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    aliases: list[tuple[str, str]] = []

    for name, ty in reg.type_table.items():
        if ty not in supported or ty.category != VkType.STRUCT:
            continue
        if name != ty.name:
            aliases.append((name, ty.name))
            continue
        if name in seen or not is_serializable(ty):
            continue
        seen.add(name)

        chain = get_chain(ty) if ty.s_type else []
        pnext_enum_name = f"{name}PNext"

        if chain:
            lines.append(f"#[derive(Clone, Debug, PartialEq)]\npub enum {pnext_enum_name} {{\n")
            for nxt in chain:
                vname = nxt.name[2:] if nxt.name.startswith("Vk") else nxt.name
                lines.append(f"    {vname}(Box<{nxt.name}>),\n")
            lines.append("}\n\n")

        # Struct definition
        large_arr = struct_has_large_array(ty)
        if large_arr:
            lines.append(f"#[derive(Clone, Debug, PartialEq)]\npub struct {name} {{\n")
        else:
            lines.append(f"#[derive(Clone, Debug, Default, PartialEq)]\npub struct {name} {{\n")

        struct_fields: list[tuple[str, str, VkVariable | None]] = []
        for var in ty.variables:
            if var.is_p_next():
                if chain:
                    lines.append(f"    pub p_next: Vec<{pnext_enum_name}>,\n")
                    struct_fields.append(("p_next", f"Vec<{pnext_enum_name}>", None))
                continue
            rty = var_rust_type(name, var)
            if rty is None:
                continue
            fn = field_name(var)
            lines.append(f"    pub {fn}: {rty},\n")
            struct_fields.append((fn, rty, var))
        lines.append("}\n\n")

        if large_arr:
            lines.append(f"impl Default for {name} {{\n    fn default() -> Self {{\n        Self {{\n")
            for fn, rty, var in struct_fields:
                if var and var.ty.is_static_array() and var.ty.decor.dim != "3][4":
                    lines.append(f"            {fn}: core::array::from_fn(|_| Default::default()),\n")
                else:
                    lines.append(f"            {fn}: Default::default(),\n")
            lines.append("        }\n    }\n}\n\n")

        vars_map = {v.name: v for v in ty.variables}
        skip_vars = 2 if ty.s_type else 0

        lines.append(f"impl {name} {{\n")

        # pNext helpers if chain
        if chain:
            lines.append(
                f"    pub fn decode_pnext(dec: &mut Decoder<'_>) -> Result<Vec<{pnext_enum_name}>, WireError> {{\n"
                f"        if !dec.read_simple_pointer()? {{\n"
                f"            return Ok(Vec::new());\n"
                f"        }}\n"
                f"        let stype = VkStructureType::decode(dec)?;\n"
                f"        let mut tail = Self::decode_pnext(dec)?;\n"
                f"        let node = match stype {{\n"
            )
            for nxt in chain:
                vname = nxt.name[2:] if nxt.name.startswith("Vk") else nxt.name
                nxt_pnext = "Vec::new()" if get_chain(nxt) else "()"
                lines.append(
                    f"            VkStructureType::{nxt.s_type} => {pnext_enum_name}::{vname}(Box::new({nxt.name}::decode_self(dec, stype, {nxt_pnext})?)),\n"
                )
            lines.append(
                f"            _ => return Err(WireError::InvalidStructureType(stype.0)),\n"
                f"        }};\n"
                f"        tail.insert(0, node);\n"
                f"        Ok(tail)\n"
                f"    }}\n\n"
            )
            lines.append(
                f"    pub fn encode_pnext<S: WireSink>(enc: &mut Encoder<S>, chain: &[{pnext_enum_name}]) -> Result<(), WireError> {{\n"
                f"        let Some((head, tail)) = chain.split_first() else {{\n"
                f"            return enc.write_simple_pointer(false);\n"
                f"        }};\n"
                f"        enc.write_simple_pointer(true)?;\n"
                f"        match head {{\n"
            )
            for nxt in chain:
                vname = nxt.name[2:] if nxt.name.startswith("Vk") else nxt.name
                lines.append(
                    f"            {pnext_enum_name}::{vname}(v) => {{\n"
                    f"                VkStructureType::{nxt.s_type}.encode(enc)?;\n"
                    f"                Self::encode_pnext(enc, tail)?;\n"
                    f"                v.encode_self(enc)\n"
                    f"            }}\n"
                )
            lines.append("        }\n    }\n\n")

            lines.append(
                f"    pub fn decode_pnext_partial(dec: &mut Decoder<'_>) -> Result<Vec<{pnext_enum_name}>, WireError> {{\n"
                f"        if !dec.read_simple_pointer()? {{\n"
                f"            return Ok(Vec::new());\n"
                f"        }}\n"
                f"        let stype = VkStructureType::decode(dec)?;\n"
                f"        let mut tail = Self::decode_pnext_partial(dec)?;\n"
                f"        let node = match stype {{\n"
            )
            for nxt in chain:
                vname = nxt.name[2:] if nxt.name.startswith("Vk") else nxt.name
                nxt_pnext = "Vec::new()" if get_chain(nxt) else "()"
                lines.append(
                    f"            VkStructureType::{nxt.s_type} => {pnext_enum_name}::{vname}(Box::new({nxt.name}::decode_partial_self(dec, stype, {nxt_pnext})?)),\n"
                )
            lines.append(
                f"            _ => return Err(WireError::InvalidStructureType(stype.0)),\n"
                f"        }};\n"
                f"        tail.insert(0, node);\n"
                f"        Ok(tail)\n"
                f"    }}\n\n"
            )
            lines.append(
                f"    pub fn encode_pnext_partial<S: WireSink>(enc: &mut Encoder<S>, chain: &[{pnext_enum_name}]) -> Result<(), WireError> {{\n"
                f"        let Some((head, tail)) = chain.split_first() else {{\n"
                f"            return enc.write_simple_pointer(false);\n"
                f"        }};\n"
                f"        enc.write_simple_pointer(true)?;\n"
                f"        match head {{\n"
            )
            for nxt in chain:
                vname = nxt.name[2:] if nxt.name.startswith("Vk") else nxt.name
                lines.append(
                    f"            {pnext_enum_name}::{vname}(v) => {{\n"
                    f"                VkStructureType::{nxt.s_type}.encode(enc)?;\n"
                    f"                Self::encode_pnext_partial(enc, tail)?;\n"
                    f"                v.encode_partial_self(enc)\n"
                    f"            }}\n"
                )
            lines.append("        }\n    }\n\n")

        # decode_self / decode / decode_partial
        if ty.s_type:
            pnext_param = f"p_next: Vec<{pnext_enum_name}>" if chain else "_p_next: ()"
            lines.append(
                f"    pub fn decode_self(dec: &mut Decoder<'_>, s_type: VkStructureType, {pnext_param}) -> Result<Self, WireError> {{\n"
            )
            for var in ty.variables[skip_vars:]:
                lines.extend(emit_struct_decode_member(ty, var, vars_map, False, "        "))
            lines.append("        Ok(Self {\n            s_type,\n")
            if chain:
                lines.append("            p_next,\n")
            for fn, _, var in struct_fields:
                if var is not None and fn != "s_type":
                    lines.append(f"            {fn},\n")
            lines.append("        })\n    }\n\n")

            lines.append("    pub fn decode(dec: &mut Decoder<'_>) -> Result<Self, WireError> {\n")
            lines.append("        let s_type = VkStructureType::decode(dec)?;\n")
            if chain:
                lines.append("        let p_next = Self::decode_pnext(dec)?;\n")
                lines.append("        Self::decode_self(dec, s_type, p_next)\n")
            else:
                lines.append("        if dec.read_simple_pointer()? { return Err(WireError::InvalidPointerFlag(1)); }\n")
                lines.append("        Self::decode_self(dec, s_type, ())\n")
            lines.append("    }\n\n")

            lines.append(
                f"    pub fn decode_partial_self(dec: &mut Decoder<'_>, s_type: VkStructureType, {pnext_param}) -> Result<Self, WireError> {{\n"
            )
            for var in ty.variables[skip_vars:]:
                lines.extend(emit_struct_decode_member(ty, var, vars_map, True, "        "))
            lines.append("        let mut out = Self::default();\n        out.s_type = s_type;\n")
            if chain:
                lines.append("        out.p_next = p_next;\n")
            lines.append("        Ok(out)\n    }\n\n")

            lines.append("    pub fn decode_partial(dec: &mut Decoder<'_>) -> Result<Self, WireError> {\n")
            lines.append("        let s_type = VkStructureType::decode(dec)?;\n")
            if chain:
                lines.append("        let p_next = Self::decode_pnext_partial(dec)?;\n")
                lines.append("        Self::decode_partial_self(dec, s_type, p_next)\n")
            else:
                lines.append("        if dec.read_simple_pointer()? { return Err(WireError::InvalidPointerFlag(1)); }\n")
                lines.append("        Self::decode_partial_self(dec, s_type, ())\n")
            lines.append("    }\n\n")

            # encode_self / encode / encode_partial_self / encode_partial
            lines.append("    pub fn encode_self<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n")
            for var in ty.variables[skip_vars:]:
                lines.extend(emit_struct_encode_member(ty, var, vars_map, False, "self.", "        "))
            lines.append("        Ok(())\n    }\n\n")

            lines.append("    pub fn encode<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n")
            lines.append("        self.s_type.encode(enc)?;\n")
            if chain:
                lines.append("        Self::encode_pnext(enc, &self.p_next)?;\n")
            else:
                lines.append("        enc.write_simple_pointer(false)?;\n")
            lines.append("        self.encode_self(enc)\n    }\n\n")

            lines.append("    pub fn encode_partial_self<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n")
            for var in ty.variables[skip_vars:]:
                lines.extend(emit_struct_encode_member(ty, var, vars_map, True, "self.", "        "))
            lines.append("        Ok(())\n    }\n\n")

            lines.append("    pub fn encode_partial<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n")
            lines.append("        self.s_type.encode(enc)?;\n")
            if chain:
                lines.append("        Self::encode_pnext_partial(enc, &self.p_next)?;\n")
            else:
                lines.append("        enc.write_simple_pointer(false)?;\n")
            lines.append("        self.encode_partial_self(enc)\n    }\n")
        else:
            lines.append("    pub fn decode(dec: &mut Decoder<'_>) -> Result<Self, WireError> {\n")
            for var in ty.variables:
                lines.extend(emit_struct_decode_member(ty, var, vars_map, False, "        "))
            lines.append("        Ok(Self {\n")
            for fn, _, var in struct_fields:
                if var is not None:
                    lines.append(f"            {fn},\n")
            lines.append("        })\n    }\n\n")

            lines.append("    pub fn decode_partial(dec: &mut Decoder<'_>) -> Result<Self, WireError> {\n")
            for var in ty.variables:
                lines.extend(emit_struct_decode_member(ty, var, vars_map, True, "        "))
            lines.append("        Ok(Self::default())\n    }\n\n")

            lines.append("    pub fn encode<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n")
            for var in ty.variables:
                lines.extend(emit_struct_encode_member(ty, var, vars_map, False, "self.", "        "))
            lines.append("        Ok(())\n    }\n\n")

            lines.append("    pub fn encode_partial<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n")
            for var in ty.variables:
                lines.extend(emit_struct_encode_member(ty, var, vars_map, True, "self.", "        "))
            lines.append("        Ok(())\n    }\n")

        lines.append("}\n\n")

    for alias, target in aliases:
        if target in seen:
            lines.append(f"pub type {alias} = {target};\n")
    return "".join(lines)


def emit_types_rs(reg: VkRegistry, supported: set[VkType]) -> str:
    header = (
        BANNER
        + "use alloc::{boxed::Box, string::String, vec::Vec};\n"
        + "use crate::generated::constants::*;\n"
        + "use crate::generated::enums::*;\n"
        + "use crate::generated::handles::*;\n"
        + "use crate::wire::{Decoder, Encoder, WireError, WireSink};\n\n"
    )
    return header + emit_unions(reg, supported) + emit_structs(reg, supported)
