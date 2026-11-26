use venus_protocol::*;

const COMPUTE_BIN: &[u8] = include_bytes!("fixtures/compute-double-plus-one.venus.bin");
const GRAPHICS_BIN: &[u8] = include_bytes!("fixtures/graphics-rgb-triangle.venus.bin");

fn decode_and_reencode_stream(stream: &[u8]) -> (Vec<VkCommandTypeEXT>, Vec<u8>) {
    let mut dec = Decoder::new(stream);
    let mut cmds = Vec::new();
    let mut enc = Encoder::new(Vec::new());

    while !dec.is_empty() {
        let pos = dec.position();
        let hdr = match roundtrip_command(&mut dec, &mut enc) {
            Ok(h) => h,
            Err(e) => panic!("failed at byte {pos} after {} cmds ({:?}): {e}", cmds.len(), cmds.last()),
        };
        cmds.push(VkCommandTypeEXT(hdr.cmd_type));
    }
    assert!(dec.is_empty());
    (cmds, enc.into_inner())
}

#[test]
fn compute_double_plus_one_byte_exact_roundtrip() {
    let (cmds, reencoded) = decode_and_reencode_stream(COMPUTE_BIN);
    assert!(!cmds.is_empty());
    assert!(cmds.contains(&VkCommandTypeEXT::VK_COMMAND_TYPE_vkAllocateMemory_EXT));
    assert!(cmds.contains(&VkCommandTypeEXT::VK_COMMAND_TYPE_vkCmdDispatch_EXT));
    assert_eq!(reencoded.len(), COMPUTE_BIN.len());
    assert_eq!(reencoded.as_slice(), COMPUTE_BIN);
}

#[test]
fn graphics_rgb_triangle_byte_exact_roundtrip() {
    let (cmds, reencoded) = decode_and_reencode_stream(GRAPHICS_BIN);
    assert!(!cmds.is_empty());
    assert!(cmds.contains(&VkCommandTypeEXT::VK_COMMAND_TYPE_vkCreateGraphicsPipelines_EXT));
    assert!(cmds.contains(&VkCommandTypeEXT::VK_COMMAND_TYPE_vkCmdDraw_EXT));
    assert_eq!(reencoded.len(), GRAPHICS_BIN.len());
    assert_eq!(reencoded.as_slice(), GRAPHICS_BIN);
}
