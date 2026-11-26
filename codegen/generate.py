#!/usr/bin/env python3
"""Pure-Python-3-stdlib code generator for venus-protocol-rs."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "upstream"))

from vkxml import VkExtension, VkRegistry, VkType  # noqa: E402

VK_XML_EXTENSION_LIST = [
    # Venus extensions
    "VK_EXT_command_serialization",
    "VK_MESA_venus_protocol",
    # promoted to VK_VERSION_1_1
    "VK_KHR_16bit_storage",
    "VK_KHR_bind_memory2",
    "VK_KHR_dedicated_allocation",
    "VK_KHR_descriptor_update_template",
    "VK_KHR_device_group",
    "VK_KHR_device_group_creation",
    "VK_KHR_external_fence",
    "VK_KHR_external_fence_capabilities",
    "VK_KHR_external_memory",
    "VK_KHR_external_memory_capabilities",
    "VK_KHR_external_semaphore",
    "VK_KHR_external_semaphore_capabilities",
    "VK_KHR_get_memory_requirements2",
    "VK_KHR_get_physical_device_properties2",
    "VK_KHR_maintenance1",
    "VK_KHR_maintenance2",
    "VK_KHR_maintenance3",
    "VK_KHR_multiview",
    "VK_KHR_relaxed_block_layout",
    "VK_KHR_sampler_ycbcr_conversion",
    "VK_KHR_shader_draw_parameters",
    "VK_KHR_storage_buffer_storage_class",
    "VK_KHR_variable_pointers",
    # promoted to VK_VERSION_1_2
    "VK_KHR_8bit_storage",
    "VK_KHR_buffer_device_address",
    "VK_KHR_create_renderpass2",
    "VK_KHR_depth_stencil_resolve",
    "VK_KHR_draw_indirect_count",
    "VK_KHR_driver_properties",
    "VK_KHR_image_format_list",
    "VK_KHR_imageless_framebuffer",
    "VK_KHR_sampler_mirror_clamp_to_edge",
    "VK_KHR_separate_depth_stencil_layouts",
    "VK_KHR_shader_atomic_int64",
    "VK_KHR_shader_float16_int8",
    "VK_KHR_shader_float_controls",
    "VK_KHR_shader_subgroup_extended_types",
    "VK_KHR_spirv_1_4",
    "VK_KHR_timeline_semaphore",
    "VK_KHR_uniform_buffer_standard_layout",
    "VK_KHR_vulkan_memory_model",
    "VK_EXT_descriptor_indexing",
    "VK_EXT_host_query_reset",
    "VK_EXT_sampler_filter_minmax",
    "VK_EXT_scalar_block_layout",
    "VK_EXT_separate_stencil_usage",
    "VK_EXT_shader_viewport_index_layer",
    # promoted to VK_VERSION_1_3
    "VK_KHR_copy_commands2",
    "VK_KHR_dynamic_rendering",
    "VK_KHR_format_feature_flags2",
    "VK_KHR_maintenance4",
    "VK_KHR_shader_integer_dot_product",
    "VK_KHR_shader_non_semantic_info",
    "VK_KHR_shader_terminate_invocation",
    "VK_KHR_synchronization2",
    "VK_KHR_zero_initialize_workgroup_memory",
    "VK_EXT_4444_formats",
    "VK_EXT_extended_dynamic_state",
    "VK_EXT_extended_dynamic_state2",
    "VK_EXT_image_robustness",
    "VK_EXT_inline_uniform_block",
    "VK_EXT_pipeline_creation_cache_control",
    "VK_EXT_pipeline_creation_feedback",
    "VK_EXT_private_data",
    "VK_EXT_shader_demote_to_helper_invocation",
    "VK_EXT_subgroup_size_control",
    "VK_EXT_texel_buffer_alignment",
    "VK_EXT_texture_compression_astc_hdr",
    "VK_EXT_tooling_info",
    "VK_EXT_ycbcr_2plane_444_formats",
    # promoted to VK_VERSION_1_4
    "VK_KHR_dynamic_rendering_local_read",
    "VK_KHR_global_priority",
    "VK_KHR_index_type_uint8",
    "VK_KHR_line_rasterization",
    "VK_KHR_load_store_op_none",
    "VK_KHR_maintenance5",
    "VK_KHR_maintenance6",
    "VK_KHR_map_memory2",
    "VK_KHR_push_descriptor",
    "VK_KHR_shader_expect_assume",
    "VK_KHR_shader_float_controls2",
    "VK_KHR_shader_subgroup_rotate",
    "VK_KHR_vertex_attribute_divisor",
    "VK_EXT_host_image_copy",
    "VK_EXT_pipeline_protected_access",
    "VK_EXT_pipeline_robustness",
    # KHR extensions
    "VK_KHR_acceleration_structure",
    "VK_KHR_calibrated_timestamps",
    "VK_KHR_compute_shader_derivatives",
    "VK_KHR_cooperative_matrix",
    "VK_KHR_copy_memory_indirect",
    "VK_KHR_deferred_host_operations",
    "VK_KHR_fragment_shader_barycentric",
    "VK_KHR_fragment_shading_rate",
    "VK_KHR_maintenance7",
    "VK_KHR_maintenance8",
    "VK_KHR_pipeline_binary",
    "VK_KHR_pipeline_executable_properties",
    "VK_KHR_pipeline_library",
    "VK_KHR_present_id",
    "VK_KHR_present_wait",
    "VK_KHR_ray_query",
    "VK_KHR_ray_tracing_maintenance1",
    "VK_KHR_ray_tracing_pipeline",
    "VK_KHR_ray_tracing_position_fetch",
    "VK_KHR_shader_clock",
    "VK_KHR_shader_maximal_reconvergence",
    "VK_KHR_shader_quad_control",
    "VK_KHR_shader_relaxed_extended_instruction",
    "VK_KHR_shader_subgroup_uniform_control_flow",
    "VK_KHR_swapchain",
    "VK_KHR_swapchain_mutable_format",
    "VK_KHR_video_decode_h264",
    "VK_KHR_video_decode_h265",
    "VK_KHR_video_decode_queue",
    "VK_KHR_video_queue",
    "VK_KHR_workgroup_memory_explicit_layout",
    # EXT extensions
    "VK_EXT_4444_formats",
    "VK_EXT_attachment_feedback_loop_dynamic_state",
    "VK_EXT_attachment_feedback_loop_layout",
    "VK_EXT_blend_operation_advanced",
    "VK_EXT_border_color_swizzle",
    "VK_EXT_calibrated_timestamps",
    "VK_EXT_color_write_enable",
    "VK_EXT_conditional_rendering",
    "VK_EXT_conservative_rasterization",
    "VK_EXT_custom_border_color",
    "VK_EXT_depth_bias_control",
    "VK_EXT_depth_clamp_control",
    "VK_EXT_depth_clamp_zero_one",
    "VK_EXT_depth_clip_control",
    "VK_EXT_depth_clip_enable",
    "VK_EXT_depth_range_unrestricted",
    "VK_EXT_descriptor_buffer",
    "VK_EXT_dynamic_rendering_unused_attachments",
    "VK_EXT_extended_dynamic_state3",
    "VK_EXT_external_memory_acquire_unmodified",
    "VK_EXT_external_memory_dma_buf",
    "VK_EXT_filter_cubic",
    "VK_EXT_fragment_shader_interlock",
    "VK_EXT_global_priority",
    "VK_EXT_global_priority_query",
    "VK_EXT_graphics_pipeline_library",
    "VK_EXT_image_2d_view_of_3d",
    "VK_EXT_image_drm_format_modifier",
    "VK_EXT_image_sliced_view_of_3d",
    "VK_EXT_image_view_min_lod",
    "VK_EXT_index_type_uint8",
    "VK_EXT_legacy_dithering",
    "VK_EXT_legacy_vertex_attributes",
    "VK_EXT_line_rasterization",
    "VK_EXT_load_store_op_none",
    "VK_EXT_memory_budget",
    "VK_EXT_mesh_shader",
    "VK_EXT_multi_draw",
    "VK_EXT_multisampled_render_to_single_sampled",
    "VK_EXT_mutable_descriptor_type",
    "VK_EXT_nested_command_buffer",
    "VK_EXT_non_seamless_cube_map",
    "VK_EXT_pci_bus_info",
    "VK_EXT_pipeline_library_group_handles",
    "VK_EXT_post_depth_coverage",
    "VK_EXT_primitive_restart_index",
    "VK_EXT_primitive_topology_list_restart",
    "VK_EXT_primitives_generated_query",
    "VK_EXT_provoking_vertex",
    "VK_EXT_queue_family_foreign",
    "VK_EXT_rasterization_order_attachment_access",
    "VK_EXT_rgba10x6_formats",
    "VK_EXT_robustness2",
    "VK_EXT_sample_locations",
    "VK_EXT_shader_atomic_float",
    "VK_EXT_shader_atomic_float2",
    "VK_EXT_shader_float8",
    "VK_EXT_shader_image_atomic_int64",
    "VK_EXT_shader_replicated_composites",
    "VK_EXT_shader_split_barrier",
    "VK_EXT_shader_stencil_export",
    "VK_EXT_shader_subgroup_ballot",
    "VK_EXT_shader_subgroup_vote",
    "VK_EXT_shader_tile_image",
    "VK_EXT_shader_uniform_buffer_unsized_array",
    "VK_EXT_transform_feedback",
    "VK_EXT_vertex_attribute_divisor",
    "VK_EXT_vertex_attribute_robustness",
    "VK_EXT_vertex_input_dynamic_state",
    "VK_EXT_ycbcr_image_arrays",
    "VK_EXT_zero_initialize_device_memory",
    # vendor extensions
    "VK_ARM_rasterization_order_attachment_access",
    "VK_GOOGLE_decorate_string",
    "VK_GOOGLE_hlsl_functionality1",
    "VK_GOOGLE_user_type",
    "VK_IMG_filter_cubic",
    "VK_NV_compute_shader_derivatives",
    "VK_VALVE_mutable_descriptor_type",
]

EXT_SET = set(VK_XML_EXTENSION_LIST)

BASETYPE_RUST = {
    "VkSampleMask": "u32",
    "VkBool32": "u32",
    "VkFlags": "u32",
    "VkFlags64": "u64",
    "VkDeviceSize": "u64",
    "VkDeviceAddress": "u64",
}

BANNER = "// This file is generated by codegen/generate.py. Do not edit manually.\n\n"


def support_type_depends(deps: str) -> bool:
    if "+" not in deps and "," not in deps:
        return deps in EXT_SET
    for or_dep in VkExtension.top_level_split(deps, ","):
        if "+" not in or_dep and or_dep in EXT_SET:
            return True
        support_or = True
        for and_dep in VkExtension.top_level_split(or_dep, "+"):
            and_dep = and_dep.removeprefix("(").removesuffix(")")
            if not support_type_depends(and_dep):
                support_or = False
                break
        if support_or:
            return True
    return False


def get_supported_types(reg: VkRegistry) -> set:
    types = []
    for feat in reg.features:
        types.extend(feat.types)
    for ext in reg.extensions:
        if ext.name not in EXT_SET:
            continue
        types.extend(ext.types)
        for key, opt_types in ext.optional_types.items():
            if support_type_depends(key):
                types.extend(opt_types)
    with_deps = set()
    for ty in types:
        if ty not in with_deps:
            with_deps.update(ty.get_dependencies())
    return with_deps


def dedupe_by_name(reg: VkRegistry, supported: set, category: int):
    canon = {}
    aliases = []
    for name, ty in reg.type_table.items():
        if ty not in supported or ty.category != category:
            continue
        if name == ty.name:
            if name not in canon:
                canon[name] = ty
        else:
            aliases.append((name, ty.name))
    return canon, aliases


def format_constant(val: str) -> tuple[str, str]:
    v = val.strip()
    if v == "(~0U)":
        return ("u32", "u32::MAX")
    if v == "(~1U)":
        return ("u32", "u32::MAX - 1")
    if v == "(~2U)":
        return ("u32", "u32::MAX - 2")
    if v == "(~0ULL)":
        return ("u64", "u64::MAX")
    if v.endswith("F") or v.endswith("f"):
        return ("f32", f"{v[:-1]}_f32")
    if v.endswith("ULL"):
        return ("u64", v[:-3])
    if v.endswith("U"):
        return ("u32", v[:-1])
    return ("usize", v)


def format_i32_const(val: str | int) -> str:
    n = int(val, 0) if isinstance(val, str) else val
    if n > 0x7FFF_FFFF:
        return f"0x{n:08X}_u32 as i32"
    return str(n)


def emit_constants(reg: VkRegistry, supported: set) -> str:
    canon, aliases = dedupe_by_name(reg, supported, 11)
    lines = [BANNER]
    for name, ty in canon.items():
        rty, rval = format_constant(ty.attrs["value"])
        lines.append(f"pub const {name}: {rty} = {rval};\n")
    for alias, target in aliases:
        if target in canon:
            rty, _ = format_constant(canon[target].attrs["value"])
            lines.append(f"pub const {alias}: {rty} = {target};\n")
    return "".join(lines)


def emit_enums(reg: VkRegistry, supported: set) -> str:
    lines = [
        BANNER,
        "use crate::wire::{Decoder, Encoder, WireError, WireSink};\n\n",
    ]
    # Basetypes
    basetypes, _ = dedupe_by_name(reg, supported, VkType.BASETYPE)
    for name in basetypes:
        if name in BASETYPE_RUST:
            lines.append(f"pub type {name} = {BASETYPE_RUST[name]};\n")
    lines.append("\n")

    # Bitmasks
    bitmasks, bm_aliases = dedupe_by_name(reg, supported, VkType.BITMASK)
    for name, ty in bitmasks.items():
        target = ty.typedef.name if ty.typedef else "VkFlags"
        lines.append(f"pub type {name} = {target};\n")
    for alias, target in bm_aliases:
        if target in bitmasks:
            lines.append(f"pub type {alias} = {target};\n")
    lines.append("\n")

    # Enums
    enums, enum_aliases = dedupe_by_name(reg, supported, VkType.ENUM)
    for name, ty in enums.items():
        if not ty.enums:
            continue
        is_64 = ty.enums.bitwidth == 64
        inner = "u64" if is_64 else "i32"
        lines.append(
            f"#[repr(transparent)]\n"
            f"#[derive(Copy, Clone, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]\n"
            f"pub struct {name}(pub {inner});\n\n"
            f"impl {name} {{\n"
        )
        for cname, cval in ty.enums.values.items():
            if is_64:
                n = int(cval, 0) if isinstance(cval, str) else cval
                lines.append(f"    pub const {cname}: Self = Self(0x{n:X});\n")
            else:
                lines.append(f"    pub const {cname}: Self = Self({format_i32_const(cval)});\n")
        if is_64:
            lines.append(
                "\n    pub fn decode(dec: &mut Decoder<'_>) -> Result<Self, WireError> {\n"
                "        Ok(Self(dec.read_u64()?))\n"
                "    }\n\n"
                "    pub fn encode<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n"
                "        enc.write_u64(self.0)\n"
                "    }\n"
            )
        else:
            lines.append(
                "\n    pub fn decode(dec: &mut Decoder<'_>) -> Result<Self, WireError> {\n"
                "        Ok(Self(dec.read_i32()?))\n"
                "    }\n\n"
                "    pub fn encode<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {\n"
                "        enc.write_i32(self.0)\n"
                "    }\n"
            )
        lines.append("}\n\n")

    for alias, target in enum_aliases:
        if target in enums and enums[target].enums:
            lines.append(f"pub type {alias} = {target};\n")
    return "".join(lines)


def emit_handles(reg: VkRegistry, supported: set) -> str:
    handles, handle_aliases = dedupe_by_name(reg, supported, VkType.HANDLE)
    lines = [
        BANNER,
        "use crate::generated::enums::VkObjectType;\n",
        "use crate::wire::{Decoder, Encoder, ObjectId, WireError, WireSink};\n\n",
    ]
    for name, _ty in handles.items():
        obj_type = "VK_OBJECT_TYPE_" + reg.upper_name(name[2:])
        lines.append(
            f"#[repr(transparent)]\n"
            f"#[derive(Copy, Clone, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]\n"
            f"pub struct {name}(pub ObjectId);\n\n"
            f"impl {name} {{\n"
            f"    pub const NULL: Self = Self(ObjectId::NULL);\n"
            f"    pub const OBJECT_TYPE: VkObjectType = VkObjectType::{obj_type};\n\n"
            f"    #[must_use]\n"
            f"    pub const fn is_null(self) -> bool {{\n"
            f"        self.0.is_null()\n"
            f"    }}\n\n"
            f"    pub fn decode(dec: &mut Decoder<'_>) -> Result<Self, WireError> {{\n"
            f"        Ok(Self(dec.read_object_id()?))\n"
            f"    }}\n\n"
            f"    pub fn encode<S: WireSink>(&self, enc: &mut Encoder<S>) -> Result<(), WireError> {{\n"
            f"        enc.write_object_id(self.0)\n"
            f"    }}\n"
            f"}}\n\n"
        )
    for alias, target in handle_aliases:
        if target in handles:
            lines.append(f"pub type {alias} = {target};\n")
    return "".join(lines)


def emit_info(reg: VkRegistry) -> str:
    exts = [e for e in reg.extensions if e.name in EXT_SET]
    exts.sort(key=lambda e: e.number)
    lines = [
        BANNER,
        f'pub const VK_XML_VERSION: &str = "{reg.vk_xml_version}";\n',
        f"pub const MAX_COMMAND_TYPE_VALUE: i32 = {reg.max_vk_command_type_value};\n\n",
        "pub const SUPPORTED_EXTENSIONS: &[(&str, u32, u32)] = &[\n",
    ]
    for ext in exts:
        ver = getattr(ext, "version", 0)
        lines.append(f'    ("{ext.name}", {ext.number}, {ver}),\n')
    lines.append("];\n")
    return "".join(lines)


def emit_mod() -> str:
    return (
        BANNER
        + "#![allow(non_camel_case_types, non_snake_case, non_upper_case_globals, unused_imports, clippy::all)]\n\n"
        + "pub mod constants;\n"
        + "pub mod enums;\n"
        + "pub mod handles;\n"
        + "pub mod info;\n\n"
        + "pub use constants::*;\n"
        + "pub use enums::*;\n"
        + "pub use handles::*;\n"
        + "pub use info::*;\n"
    )


def main() -> None:
    xml_dir = ROOT / "upstream" / "xmls"
    reg = VkRegistry.parse(
        xml_dir / "vk.xml",
        [
            xml_dir / "VK_EXT_command_serialization.xml",
            xml_dir / "VK_MESA_venus_protocol.xml",
        ],
    )
    supported = get_supported_types(reg)
    out_dir = ROOT / "src" / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "mod.rs").write_text(emit_mod(), encoding="utf-8")
    (out_dir / "constants.rs").write_text(emit_constants(reg, supported), encoding="utf-8")
    (out_dir / "enums.rs").write_text(emit_enums(reg, supported), encoding="utf-8")
    (out_dir / "handles.rs").write_text(emit_handles(reg, supported), encoding="utf-8")
    (out_dir / "info.rs").write_text(emit_info(reg), encoding="utf-8")
    print(f"Generated src/generated/ ({len(supported)} supported types)")


if __name__ == "__main__":
    main()
