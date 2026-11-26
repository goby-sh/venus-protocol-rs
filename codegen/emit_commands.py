"""Generate src/generated/commands.rs and src/generated/dispatch.rs."""

from __future__ import annotations

from vkxml import VkRegistry, VkType, VkVariable
from emit_protocol import (
    BANNER,
    COMMAND_BLOCK_LIST,
    emit_scalar_decode,
    emit_scalar_encode,
    emit_struct_decode_member,
    emit_struct_encode_member,
    field_name,
    is_serializable,
    resolve_base,
    rust_base_type,
    to_snake,
    var_rust_type,
)


def cmd_pascal(name: str) -> str:
    return name[0].upper() + name[1:]


def emit_cmd_arg_decode(cmd: VkType, var: VkVariable, is_out_only: bool) -> list[str]:
    if not is_out_only:
        return emit_struct_decode_member(cmd, var, {}, False, "        ")
    # Out-only parameter in request: only pointer/array_size/partial is on the wire
    fn = field_name(var)
    if not is_serializable(var):
        if var.ty.is_pointer():
            return [f"        if dec.read_simple_pointer()? {{ return Err(WireError::InvalidPointerFlag(1)); }}\n"]
        return []
    base = var.ty.base
    if var.ty.is_pointer():
        if var.is_dynamic_array():
            if base.category == base.HANDLE:
                return [
                    f"        let {fn}_sz = dec.read_array_size_unchecked()?;\n"
                    f"        let mut {fn} = Vec::with_capacity({fn}_sz as usize);\n"
                    f"        for _ in 0..{fn}_sz {{ {fn}.push({base.name}::decode(dec)?); }}\n"
                ]
            if base.category == base.STRUCT:
                return [
                    f"        let {fn}_sz = dec.read_array_size_unchecked()?;\n"
                    f"        let mut {fn} = Vec::with_capacity({fn}_sz as usize);\n"
                    f"        for _ in 0..{fn}_sz {{ {fn}.push({base.name}::decode_partial(dec)?); }}\n"
                ]
            return [
                f"        let {fn}_sz = dec.read_array_size_unchecked()?;\n"
                f"        let {fn} = Vec::with_capacity({fn}_sz as usize);\n"
            ]
        if base.category == base.STRUCT:
            return [
                f"        let {fn} = if dec.read_simple_pointer()? {{ Some(Box::new({base.name}::decode_partial(dec)?)) }} else {{ None }};\n"
            ]
        if base.category == base.HANDLE:
            return [
                f"        let {fn} = if dec.read_simple_pointer()? {{ Some(Box::new({base.name}::decode(dec)?)) }} else {{ None }};\n"
            ]
        return [
            f"        let {fn} = if dec.read_simple_pointer()? {{ Some(Box::new(Default::default())) }} else {{ None }};\n"
        ]
    return []


def emit_cmd_arg_encode(cmd: VkType, var: VkVariable, is_out_only: bool) -> list[str]:
    if not is_out_only:
        return emit_struct_encode_member(cmd, var, {}, False, "self.", "        ")
    fn = field_name(var)
    if not is_serializable(var):
        if var.ty.is_pointer():
            return ["        enc.write_simple_pointer(false)?;\n"]
        return []
    base = var.ty.base
    if var.ty.is_pointer():
        if var.is_dynamic_array():
            if base.category == base.HANDLE:
                return [
                    f"        enc.write_array_size(self.{fn}.len() as u64)?;\n"
                    f"        for item in &self.{fn} {{ item.encode(enc)?; }}\n"
                ]
            if base.category == base.STRUCT:
                return [
                    f"        enc.write_array_size(self.{fn}.len() as u64)?;\n"
                    f"        for item in &self.{fn} {{ item.encode_partial(enc)?; }}\n"
                ]
            return [f"        enc.write_array_size(self.{fn}.len() as u64)?;\n"]
        if base.category == base.STRUCT:
            return [
                f"        match &self.{fn} {{\n"
                f"            None => enc.write_simple_pointer(false)?,\n"
                f"            Some(v) => {{ enc.write_simple_pointer(true)?; v.encode_partial(enc)?; }}\n"
                f"        }}\n"
            ]
        if base.category == base.HANDLE:
            return [
                f"        match &self.{fn} {{\n"
                f"            None => enc.write_simple_pointer(false)?,\n"
                f"            Some(v) => {{ enc.write_simple_pointer(true)?; v.encode(enc)?; }}\n"
                f"        }}\n"
            ]
        return [f"        enc.write_simple_pointer(self.{fn}.is_some())?;\n"]
    return []


def emit_commands_rs(reg: VkRegistry, supported: set[VkType]) -> str:
    lines = [
        BANNER,
        "use alloc::{boxed::Box, string::String, vec::Vec};\n",
        "use crate::generated::enums::*;\n",
        "use crate::generated::handles::*;\n",
        "use crate::generated::types::*;\n",
        "use crate::wire::{CommandFlags, CommandHeader, Decoder, Encoder, WireError, WireSink};\n\n",
    ]
    cmd_enum_vals = reg.type_table["VkCommandTypeEXT"].enums.values
    seen: set[str] = set()
    for name, ty in reg.type_table.items():
        if ty not in supported or ty.category != VkType.COMMAND or name != ty.name or name in seen:
            continue
        if not is_serializable(ty) or ty.attrs.get("c_type") not in cmd_enum_vals:
            continue
        seen.add(name)

        req_name = f"{cmd_pascal(name)}Request"
        rep_name = f"{cmd_pascal(name)}Reply"
        cmd_enum = ty.attrs["c_type"]

        # Request struct
        req_fields: list[tuple[str, str, VkVariable, bool]] = []
        lines.append(f"#[derive(Clone, Debug, Default, PartialEq)]\npub struct {req_name} {{\n")
        for var in ty.variables:
            rty = var_rust_type(name, var)
            if rty is None:
                continue
            fn = field_name(var)
            is_out_only = ("var_out" in var.attrs) and ("var_in" not in var.attrs)
            req_fields.append((fn, rty, var, is_out_only))
            lines.append(f"    pub {fn}: {rty},\n")
        lines.append("}\n\n")

        lines.append(f"impl {req_name} {{\n")
        lines.append("    pub fn decode(dec: &mut Decoder<'_>) -> Result<Self, WireError> {\n")
        for var in ty.variables:
            is_out_only = ("var_out" in var.attrs) and ("var_in" not in var.attrs)
            lines.extend(emit_cmd_arg_decode(ty, var, is_out_only))
        lines.append("        Ok(Self {\n")
        for fn, _, _, _ in req_fields:
            lines.append(f"            {fn},\n")
        lines.append("        })\n    }\n\n")

        lines.append("    pub fn encode<S: WireSink>(&self, enc: &mut Encoder<S>, flags: CommandFlags) -> Result<(), WireError> {\n")
        lines.append(f"        enc.write_command_header(CommandHeader {{ cmd_type: VkCommandTypeEXT::{cmd_enum}.0, flags }})?;\n")
        for var in ty.variables:
            is_out_only = ("var_out" in var.attrs) and ("var_in" not in var.attrs)
            lines.extend(emit_cmd_arg_encode(ty, var, is_out_only))
        lines.append("        Ok(())\n    }\n}\n\n")

        # Reply struct
        out_vars = [v for v in ty.variables if "var_out" in v.attrs and is_serializable(v)]
        lines.append(f"#[derive(Clone, Debug, Default, PartialEq)]\npub struct {rep_name} {{\n")
        if ty.ret:
            lines.append(f"    pub ret: {rust_base_type(ty.ret.ty.base)},\n")
        for var in out_vars:
            rty = var_rust_type(name, var)
            if rty:
                lines.append(f"    pub {field_name(var)}: {rty},\n")
        lines.append("}\n\n")

        lines.append(f"impl {rep_name} {{\n")
        lines.append("    pub fn encode<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n")
        lines.append(f"        enc.write_reply_header(VkCommandTypeEXT::{cmd_enum}.0)?;\n")
        if ty.ret:
            lines.append(f"        {emit_scalar_encode(ty.ret.ty.base, 'self.ret')};\n")
        for var in out_vars:
            lines.extend(emit_struct_encode_member(ty, var, {}, False, "self.", "        "))
        lines.append("        Ok(())\n    }\n\n")

        lines.append("    pub fn decode(dec: &mut Decoder<'_>) -> Result<Self, WireError> {\n")
        lines.append(
            f"        let cmd = dec.read_reply_header()?;\n"
            f"        if cmd != VkCommandTypeEXT::{cmd_enum}.0 {{\n"
            f"            return Err(WireError::UnsupportedCommand(cmd));\n"
            f"        }}\n"
        )
        if ty.ret:
            lines.append(f"        let ret = {emit_scalar_decode(ty.ret.ty.base)};\n")
        for var in out_vars:
            lines.extend(emit_struct_decode_member(ty, var, {}, False, "        "))
        lines.append("        Ok(Self {\n")
        if ty.ret:
            lines.append("            ret,\n")
        for var in out_vars:
            lines.append(f"            {field_name(var)},\n")
        lines.append("        })\n    }\n}\n\n")

    return "".join(lines)


def emit_dispatch_rs(reg: VkRegistry, supported: set[VkType]) -> str:
    lines = [
        BANNER,
        "use crate::generated::commands::*;\n",
        "use crate::generated::enums::VkCommandTypeEXT;\n",
        "use crate::wire::{CommandHeader, Decoder, Encoder, WireError, WireSink};\n\n",
        "pub trait VenusHandler {\n",
    ]
    cmds: list[VkType] = []
    cmd_enum_vals = reg.type_table["VkCommandTypeEXT"].enums.values
    seen: set[str] = set()
    for name, ty in reg.type_table.items():
        if ty not in supported or ty.category != VkType.COMMAND or name != ty.name or name in seen:
            continue
        if not is_serializable(ty) or ty.attrs.get("c_type") not in cmd_enum_vals:
            continue
        seen.add(name)
        cmds.append(ty)
        mname = to_snake(name)
        req_name = f"{cmd_pascal(name)}Request"
        rep_name = f"{cmd_pascal(name)}Reply"
        lines.append(
            f"    fn {mname}(&mut self, _req: {req_name}) -> Result<{rep_name}, WireError> {{\n"
            f"        Err(WireError::UnsupportedCommand(VkCommandTypeEXT::{ty.attrs['c_type']}.0))\n"
            f"    }}\n"
        )
    lines.append("}\n\n")

    lines.append(
        "pub fn dispatch_command<S: WireSink>(\n"
        "    dec: &mut Decoder<'_>,\n"
        "    reply_enc: Option<&mut Encoder<S>>,\n"
        "    handler: &mut impl VenusHandler,\n"
        ") -> Result<CommandHeader, WireError> {\n"
        "    let header = dec.read_command_header()?;\n"
        "    match VkCommandTypeEXT(header.cmd_type) {\n"
    )
    for ty in cmds:
        mname = to_snake(ty.name)
        req_name = f"{cmd_pascal(ty.name)}Request"
        pats = [f"VkCommandTypeEXT::{ty.attrs['c_type']}"]
        for alias in ty.aliases:
            pats.append(f"VkCommandTypeEXT::VK_COMMAND_TYPE_{alias}_EXT")
        pat_str = " | ".join(pats)
        lines.append(
            f"        {pat_str} => {{\n"
            f"            let req = {req_name}::decode(dec)?;\n"
            f"            let rep = handler.{mname}(req)?;\n"
            f"            if header.flags.wants_reply() {{\n"
            f"                if let Some(enc) = reply_enc {{ rep.encode(enc)?; }}\n"
            f"            }}\n"
            f"        }}\n"
        )
    lines.append(
        "        _ => return Err(WireError::UnsupportedCommand(header.cmd_type)),\n"
        "    }\n"
        "    Ok(header)\n"
        "}\n\n"
        "/// Decodes one command request from `dec` and re-encodes it into `enc`.\n"
        "pub fn roundtrip_command<S: WireSink>(\n"
        "    dec: &mut Decoder<'_>,\n"
        "    enc: &mut Encoder<S>,\n"
        ") -> Result<CommandHeader, WireError> {\n"
        "    let header = dec.read_command_header()?;\n"
        "    match VkCommandTypeEXT(header.cmd_type) {\n"
    )
    for ty in cmds:
        req_name = f"{cmd_pascal(ty.name)}Request"
        pats = [f"VkCommandTypeEXT::{ty.attrs['c_type']}"]
        for alias in ty.aliases:
            pats.append(f"VkCommandTypeEXT::VK_COMMAND_TYPE_{alias}_EXT")
        pat_str = " | ".join(pats)
        lines.append(
            f"        {pat_str} => {{\n"
            f"            let req = {req_name}::decode(dec)?;\n"
            f"            req.encode(enc, header.flags)?;\n"
            f"        }}\n"
        )
    lines.append(
        "        _ => return Err(WireError::UnsupportedCommand(header.cmd_type)),\n"
        "    }\n"
        "    Ok(header)\n"
        "}\n"
    )
    return "".join(lines)
