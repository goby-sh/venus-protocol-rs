#![cfg_attr(not(feature = "std"), no_std)]

pub const WIRE_FORMAT_VERSION: u32 = 1;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wire_format_version_is_v1() {
        assert_eq!(WIRE_FORMAT_VERSION, 1);
    }
}
