use venus_protocol::*;

#[test]
fn nested_pnext_chain_roundtrip() {
    let info = VkBufferCreateInfo {
        s_type: VkStructureType::VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
        p_next: vec![
            VkBufferCreateInfoPNext::BufferOpaqueCaptureAddressCreateInfo(Box::new(
                VkBufferOpaqueCaptureAddressCreateInfo {
                    s_type: VkStructureType::VK_STRUCTURE_TYPE_BUFFER_OPAQUE_CAPTURE_ADDRESS_CREATE_INFO,
                    opaque_capture_address: 0xDEAD_BEEF_0000_1000,
                },
            )),
            VkBufferCreateInfoPNext::ExternalMemoryBufferCreateInfo(Box::new(
                VkExternalMemoryBufferCreateInfo {
                    s_type: VkStructureType::VK_STRUCTURE_TYPE_EXTERNAL_MEMORY_BUFFER_CREATE_INFO,
                    handle_types: 0x1,
                },
            )),
        ],
        flags: 0,
        size: 4096,
        usage: 0x20,
        sharing_mode: VkSharingMode::VK_SHARING_MODE_EXCLUSIVE,
        queue_family_index_count: 0,
        p_queue_family_indices: Vec::new(),
    };

    let mut enc = Encoder::new(Vec::new());
    info.encode(&mut enc).unwrap();
    let bytes = enc.into_inner();

    let mut dec = Decoder::new(&bytes);
    let decoded = VkBufferCreateInfo::decode(&mut dec).unwrap();
    assert!(dec.is_empty());
    assert_eq!(decoded, info);
}

#[test]
fn union_and_blob_command_roundtrip() {
    let req = VkCmdPushConstantsRequest {
        command_buffer: VkCommandBuffer(ObjectId(42)),
        layout: VkPipelineLayout(ObjectId(7)),
        stage_flags: 1,
        offset: 0,
        size: 5,
        p_values: vec![1, 2, 3, 4, 5],
    };

    let mut enc = Encoder::new(Vec::new());
    req.encode(&mut enc, CommandFlags::empty()).unwrap();
    let bytes = enc.into_inner();

    let mut dec = Decoder::new(&bytes);
    let hdr = dec.read_command_header().unwrap();
    assert_eq!(hdr.cmd_type, VkCommandTypeEXT::VK_COMMAND_TYPE_vkCmdPushConstants_EXT.0);
    let decoded = VkCmdPushConstantsRequest::decode(&mut dec).unwrap();
    assert!(dec.is_empty());
    assert_eq!(decoded, req);

    let clear = VkClearValue::Color(VkClearColorValue::Float32([1.0, 0.5, 0.25, 1.0]));
    let mut enc2 = Encoder::new(Vec::new());
    clear.encode(&mut enc2).unwrap();
    let clear_bytes = enc2.into_inner();
    let mut dec2 = Decoder::new(&clear_bytes);
    assert_eq!(VkClearValue::decode(&mut dec2).unwrap(), clear);
    assert!(dec2.is_empty());
}

#[test]
fn reply_and_dispatch_roundtrip() {
    struct TestHandler;
    impl VenusHandler for TestHandler {
        fn vk_create_buffer(&mut self, req: VkCreateBufferRequest) -> Result<VkCreateBufferReply, WireError> {
            assert_eq!(req.p_create_info.as_ref().unwrap().size, 1024);
            Ok(VkCreateBufferReply {
                ret: VkResult::VK_SUCCESS,
                p_buffer: req.p_buffer,
            })
        }
    }

    let req = VkCreateBufferRequest {
        device: VkDevice(ObjectId(1)),
        p_create_info: Some(Box::new(VkBufferCreateInfo {
            s_type: VkStructureType::VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
            size: 1024,
            ..Default::default()
        })),
        p_buffer: Some(Box::new(VkBuffer(ObjectId(99)))),
    };

    let mut req_enc = Encoder::new(Vec::new());
    req.encode(&mut req_enc, CommandFlags::generate_reply()).unwrap();
    let req_bytes = req_enc.into_inner();

    let mut dec = Decoder::new(&req_bytes);
    let mut rep_enc = Encoder::new(Vec::new());
    let mut handler = TestHandler;
    let hdr = dispatch_command(&mut dec, Some(&mut rep_enc), &mut handler).unwrap();
    assert!(hdr.flags.wants_reply());
    assert!(dec.is_empty());

    let rep_bytes = rep_enc.into_inner();
    let mut rep_dec = Decoder::new(&rep_bytes);
    let rep = VkCreateBufferReply::decode(&mut rep_dec).unwrap();
    assert!(rep_dec.is_empty());
    assert_eq!(rep.ret, VkResult::VK_SUCCESS);
    assert_eq!(rep.p_buffer, Some(Box::new(VkBuffer(ObjectId(99)))));
}
