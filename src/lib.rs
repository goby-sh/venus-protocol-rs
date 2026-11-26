#![cfg_attr(not(feature = "std"), no_std)]

#[cfg(feature = "alloc")]
extern crate alloc;

pub mod generated;
pub mod wire;

pub use generated::*;
pub use wire::*;

pub const WIRE_FORMAT_VERSION: u32 = 1;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wire_format_version_is_v1() {
        assert_eq!(WIRE_FORMAT_VERSION, 1);
    }

    #[test]
    fn generated_command_types_and_round_trip() {
        assert_eq!(VkCommandTypeEXT::VK_COMMAND_TYPE_vkCreateInstance_EXT.0, 0);

        let mut enc = Encoder::new(Vec::new());
        VkCommandTypeEXT::VK_COMMAND_TYPE_vkCreateBuffer_EXT
            .encode(&mut enc)
            .unwrap();
        VkCommandTypeEXT::VK_COMMAND_TYPE_vkCmdDispatch_EXT
            .encode(&mut enc)
            .unwrap();
        VkCommandTypeEXT::VK_COMMAND_TYPE_vkSetReplyCommandStreamMESA_EXT
            .encode(&mut enc)
            .unwrap();
        let bytes = enc.into_inner();

        let mut dec = Decoder::new(&bytes);
        assert_eq!(
            VkCommandTypeEXT::decode(&mut dec).unwrap(),
            VkCommandTypeEXT::VK_COMMAND_TYPE_vkCreateBuffer_EXT
        );
        assert_eq!(
            VkCommandTypeEXT::decode(&mut dec).unwrap(),
            VkCommandTypeEXT::VK_COMMAND_TYPE_vkCmdDispatch_EXT
        );
        assert_eq!(
            VkCommandTypeEXT::decode(&mut dec).unwrap(),
            VkCommandTypeEXT::VK_COMMAND_TYPE_vkSetReplyCommandStreamMESA_EXT
        );
        assert!(dec.is_empty());
    }

    #[test]
    fn generated_enums_handles_and_info() {
        assert_eq!(VkResult::VK_SUCCESS.0, 0);
        assert_eq!(VkResult::VK_ERROR_OUT_OF_HOST_MEMORY.0, -1);
        assert_eq!(
            VkStructureType::VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO.0,
            1
        );
        assert!(VkBuffer::NULL.is_null());
        assert_eq!(VkBuffer::OBJECT_TYPE, VkObjectType::VK_OBJECT_TYPE_BUFFER);

        // 64-bit enum round-trip
        let mut enc = Encoder::new(Vec::new());
        VkAccessFlagBits2::VK_ACCESS_2_SHADER_WRITE_BIT
            .encode(&mut enc)
            .unwrap();
        let bytes = enc.into_inner();
        assert_eq!(bytes.len(), 8);
        let mut dec = Decoder::new(&bytes);
        assert_eq!(
            VkAccessFlagBits2::decode(&mut dec).unwrap(),
            VkAccessFlagBits2::VK_ACCESS_2_SHADER_WRITE_BIT
        );

        assert!(!SUPPORTED_EXTENSIONS.is_empty());
        assert!(
            SUPPORTED_EXTENSIONS
                .iter()
                .any(|(name, _, _)| *name == "VK_MESA_venus_protocol")
        );
        assert!(
            SUPPORTED_EXTENSIONS
                .iter()
                .any(|(name, _, _)| *name == "VK_EXT_command_serialization")
        );
    }
}
