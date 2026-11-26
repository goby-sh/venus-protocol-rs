use core::fmt;

#[cfg(feature = "alloc")]
use alloc::{string::String, vec::Vec};

/// Errors produced while decoding or encoding Venus wire-protocol streams.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum WireError {
    UnexpectedEof,
    BufferTooSmall,
    InvalidArraySize { expected: u64, actual: u64 },
    InvalidPointerFlag(u64),
    InvalidString,
    LengthOverflow,
    UnsupportedCommand(i32),
    InvalidStructureType(i32),
    TrailingBytes(usize),
}

impl fmt::Display for WireError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnexpectedEof => write!(f, "unexpected end of wire stream"),
            Self::BufferTooSmall => write!(f, "output buffer too small"),
            Self::InvalidArraySize { expected, actual } => {
                write!(f, "invalid array size: expected {expected}, got {actual}")
            }
            Self::InvalidPointerFlag(v) => write!(f, "invalid simple pointer flag: {v}"),
            Self::InvalidString => write!(f, "invalid UTF-8 or NUL-terminated string"),
            Self::LengthOverflow => write!(f, "wire length overflow"),
            Self::UnsupportedCommand(cmd) => write!(f, "unsupported Venus command: {cmd}"),
            Self::InvalidStructureType(stype) => write!(f, "invalid VkStructureType: {stype}"),
            Self::TrailingBytes(n) => write!(f, "{n} trailing bytes remaining in stream"),
        }
    }
}

impl core::error::Error for WireError {}

/// 64-bit Venus object identifier.
#[repr(transparent)]
#[derive(Copy, Clone, Debug, Default, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct ObjectId(pub u64);

impl ObjectId {
    pub const NULL: Self = Self(0);

    #[must_use]
    pub const fn is_null(self) -> bool {
        self.0 == 0
    }
}

/// Command flags encoded in every Venus command header.
#[repr(transparent)]
#[derive(Copy, Clone, Debug, Default, PartialEq, Eq)]
pub struct CommandFlags(pub u32);

impl CommandFlags {
    pub const GENERATE_REPLY_BIT: u32 = 0x0000_0001;

    #[must_use]
    pub const fn empty() -> Self {
        Self(0)
    }

    #[must_use]
    pub const fn generate_reply() -> Self {
        Self(Self::GENERATE_REPLY_BIT)
    }

    #[must_use]
    pub const fn wants_reply(self) -> bool {
        (self.0 & Self::GENERATE_REPLY_BIT) != 0
    }
}

/// 8-byte Venus command header (`VkCommandTypeEXT` + `VkCommandFlagsEXT`).
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub struct CommandHeader {
    pub cmd_type: i32,
    pub flags: CommandFlags,
}

/// Aligns `len` up to a 4-byte boundary, returning `None` on `usize` overflow.
#[must_use]
pub const fn align4(len: usize) -> Option<usize> {
    match len.checked_add(3) {
        Some(n) => Some(n & !3),
        None => None,
    }
}

/// Returns the padded wire byte length of an opaque blob of `len` bytes.
#[must_use]
pub const fn sizeof_blob(len: usize) -> Option<usize> {
    align4(len)
}

/// Returns the padded wire byte length of `count` scalar elements of `elem_size` bytes.
#[must_use]
pub const fn sizeof_scalar_array(elem_size: usize, count: usize) -> Option<usize> {
    match elem_size.checked_mul(count) {
        Some(total) => align4(total),
        None => None,
    }
}

/// Bounds-checked little-endian Venus wire decoder over a byte slice.
#[derive(Debug, Clone)]
pub struct Decoder<'a> {
    buf: &'a [u8],
    pos: usize,
}

impl<'a> Decoder<'a> {
    #[must_use]
    pub const fn new(buf: &'a [u8]) -> Self {
        Self { buf, pos: 0 }
    }

    #[must_use]
    pub const fn position(&self) -> usize {
        self.pos
    }

    #[must_use]
    pub const fn remaining(&self) -> usize {
        self.buf.len().saturating_sub(self.pos)
    }

    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.remaining() == 0
    }

    pub fn peek_i32(&self) -> Result<i32, WireError> {
        let bytes = self.peek_bytes(4)?;
        Ok(i32::from_le_bytes([bytes[0], bytes[1], bytes[2], bytes[3]]))
    }

    pub fn peek_u64(&self) -> Result<u64, WireError> {
        let bytes = self.peek_bytes(8)?;
        Ok(u64::from_le_bytes([
            bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7],
        ]))
    }

    fn peek_bytes(&self, len: usize) -> Result<&'a [u8], WireError> {
        let end = self.pos.checked_add(len).ok_or(WireError::LengthOverflow)?;
        self.buf.get(self.pos..end).ok_or(WireError::UnexpectedEof)
    }

    fn take_bytes(&mut self, len: usize) -> Result<&'a [u8], WireError> {
        let end = self.pos.checked_add(len).ok_or(WireError::LengthOverflow)?;
        let slice = self.buf.get(self.pos..end).ok_or(WireError::UnexpectedEof)?;
        self.pos = end;
        Ok(slice)
    }

    fn take_aligned(&mut self, len: usize) -> Result<&'a [u8], WireError> {
        let wire_len = align4(len).ok_or(WireError::LengthOverflow)?;
        let padded = self.take_bytes(wire_len)?;
        Ok(&padded[..len])
    }

    pub fn read_u8(&mut self) -> Result<u8, WireError> {
        let b = self.take_bytes(4)?;
        Ok(b[0])
    }

    pub fn read_i8(&mut self) -> Result<i8, WireError> {
        Ok(self.read_u8()? as i8)
    }

    pub fn read_u16(&mut self) -> Result<u16, WireError> {
        let b = self.take_bytes(4)?;
        Ok(u16::from_le_bytes([b[0], b[1]]))
    }

    pub fn read_i16(&mut self) -> Result<i16, WireError> {
        Ok(self.read_u16()? as i16)
    }

    pub fn read_u32(&mut self) -> Result<u32, WireError> {
        let b = self.take_bytes(4)?;
        Ok(u32::from_le_bytes([b[0], b[1], b[2], b[3]]))
    }

    pub fn read_i32(&mut self) -> Result<i32, WireError> {
        let b = self.take_bytes(4)?;
        Ok(i32::from_le_bytes([b[0], b[1], b[2], b[3]]))
    }

    pub fn read_u64(&mut self) -> Result<u64, WireError> {
        let b = self.take_bytes(8)?;
        Ok(u64::from_le_bytes([
            b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7],
        ]))
    }

    pub fn read_i64(&mut self) -> Result<i64, WireError> {
        let b = self.take_bytes(8)?;
        Ok(i64::from_le_bytes([
            b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7],
        ]))
    }

    pub fn read_f32(&mut self) -> Result<f32, WireError> {
        Ok(f32::from_bits(self.read_u32()?))
    }

    pub fn read_f64(&mut self) -> Result<f64, WireError> {
        Ok(f64::from_bits(self.read_u64()?))
    }

    pub fn read_bool32(&mut self) -> Result<bool, WireError> {
        Ok(self.read_u32()? != 0)
    }

    /// Reads a wire `size_t` (always encoded as 64-bit `u64`).
    pub fn read_size_t(&mut self) -> Result<u64, WireError> {
        self.read_u64()
    }

    pub fn read_object_id(&mut self) -> Result<ObjectId, WireError> {
        Ok(ObjectId(self.read_u64()?))
    }

    pub fn read_array_size(&mut self, expected: u64) -> Result<u64, WireError> {
        let actual = self.read_u64()?;
        if actual != expected {
            return Err(WireError::InvalidArraySize { expected, actual });
        }
        Ok(actual)
    }

    pub fn read_array_size_unchecked(&mut self) -> Result<u64, WireError> {
        self.read_u64()
    }

    pub fn read_simple_pointer(&mut self) -> Result<bool, WireError> {
        match self.read_u64()? {
            0 => Ok(false),
            1 => Ok(true),
            other => Err(WireError::InvalidPointerFlag(other)),
        }
    }

    pub fn read_blob(&mut self, len: usize) -> Result<&'a [u8], WireError> {
        self.take_aligned(len)
    }

    /// Reads a `len`-byte NUL-terminated C string (wire-padded to 4 bytes) and
    /// returns the slice up to the first NUL byte.
    pub fn read_cstr_bytes(&mut self, len: usize) -> Result<&'a [u8], WireError> {
        if len == 0 {
            return Err(WireError::InvalidString);
        }
        let raw = self.take_aligned(len)?;
        let nul_pos = raw.iter().position(|&b| b == 0).unwrap_or(raw.len());
        Ok(&raw[..nul_pos])
    }

    pub fn read_command_header(&mut self) -> Result<CommandHeader, WireError> {
        let cmd_type = self.read_i32()?;
        let flags = CommandFlags(self.read_u32()?);
        Ok(CommandHeader { cmd_type, flags })
    }

    pub fn read_reply_header(&mut self) -> Result<i32, WireError> {
        self.read_i32()
    }

    pub fn read_u8_slice(&mut self, count: usize) -> Result<&'a [u8], WireError> {
        self.take_aligned(count)
    }

    #[cfg(feature = "alloc")]
    pub fn read_u16_vec(&mut self, count: usize) -> Result<Vec<u16>, WireError> {
        let byte_len = count.checked_mul(2).ok_or(WireError::LengthOverflow)?;
        let raw = self.take_aligned(byte_len)?;
        let mut out = Vec::with_capacity(count);
        for chunk in raw.chunks_exact(2) {
            out.push(u16::from_le_bytes([chunk[0], chunk[1]]));
        }
        Ok(out)
    }

    #[cfg(feature = "alloc")]
    pub fn read_u32_vec(&mut self, count: usize) -> Result<Vec<u32>, WireError> {
        let byte_len = count.checked_mul(4).ok_or(WireError::LengthOverflow)?;
        let raw = self.take_bytes(byte_len)?;
        let mut out = Vec::with_capacity(count);
        for chunk in raw.chunks_exact(4) {
            out.push(u32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]));
        }
        Ok(out)
    }

    #[cfg(feature = "alloc")]
    pub fn read_i32_vec(&mut self, count: usize) -> Result<Vec<i32>, WireError> {
        let byte_len = count.checked_mul(4).ok_or(WireError::LengthOverflow)?;
        let raw = self.take_bytes(byte_len)?;
        let mut out = Vec::with_capacity(count);
        for chunk in raw.chunks_exact(4) {
            out.push(i32::from_le_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]));
        }
        Ok(out)
    }

    #[cfg(feature = "alloc")]
    pub fn read_u64_vec(&mut self, count: usize) -> Result<Vec<u64>, WireError> {
        let byte_len = count.checked_mul(8).ok_or(WireError::LengthOverflow)?;
        let raw = self.take_bytes(byte_len)?;
        let mut out = Vec::with_capacity(count);
        for chunk in raw.chunks_exact(8) {
            out.push(u64::from_le_bytes([
                chunk[0], chunk[1], chunk[2], chunk[3], chunk[4], chunk[5], chunk[6], chunk[7],
            ]));
        }
        Ok(out)
    }

    #[cfg(feature = "alloc")]
    pub fn read_f32_vec(&mut self, count: usize) -> Result<Vec<f32>, WireError> {
        let byte_len = count.checked_mul(4).ok_or(WireError::LengthOverflow)?;
        let raw = self.take_bytes(byte_len)?;
        let mut out = Vec::with_capacity(count);
        for chunk in raw.chunks_exact(4) {
            out.push(f32::from_bits(u32::from_le_bytes([
                chunk[0], chunk[1], chunk[2], chunk[3],
            ])));
        }
        Ok(out)
    }

    #[cfg(feature = "alloc")]
    pub fn read_object_id_vec(&mut self, count: usize) -> Result<Vec<ObjectId>, WireError> {
        let byte_len = count.checked_mul(8).ok_or(WireError::LengthOverflow)?;
        let raw = self.take_bytes(byte_len)?;
        let mut out = Vec::with_capacity(count);
        for chunk in raw.chunks_exact(8) {
            out.push(ObjectId(u64::from_le_bytes([
                chunk[0], chunk[1], chunk[2], chunk[3], chunk[4], chunk[5], chunk[6], chunk[7],
            ])));
        }
        Ok(out)
    }

    #[cfg(feature = "alloc")]
    pub fn read_string(&mut self, len: usize) -> Result<String, WireError> {
        let bytes = self.read_cstr_bytes(len)?;
        let s = core::str::from_utf8(bytes).map_err(|_| WireError::InvalidString)?;
        Ok(String::from(s))
    }
}

/// Destination sink for [`Encoder`].
pub trait WireSink {
    /// Writes `data` followed by `wire_len - data.len()` zero-padding bytes.
    fn write_aligned(&mut self, data: &[u8], wire_len: usize) -> Result<(), WireError>;
}

/// Fixed-capacity `no_std` sink backed by a mutable byte slice.
#[derive(Debug)]
pub struct SliceSink<'a> {
    buf: &'a mut [u8],
    pos: usize,
}

impl<'a> SliceSink<'a> {
    #[must_use]
    pub fn new(buf: &'a mut [u8]) -> Self {
        Self { buf, pos: 0 }
    }

    #[must_use]
    pub const fn written(&self) -> usize {
        self.pos
    }

    #[must_use]
    pub fn as_slice(&self) -> &[u8] {
        &self.buf[..self.pos]
    }
}

impl WireSink for SliceSink<'_> {
    fn write_aligned(&mut self, data: &[u8], wire_len: usize) -> Result<(), WireError> {
        if wire_len < data.len() {
            return Err(WireError::LengthOverflow);
        }
        let end = self.pos.checked_add(wire_len).ok_or(WireError::LengthOverflow)?;
        if end > self.buf.len() {
            return Err(WireError::BufferTooSmall);
        }
        self.buf[self.pos..self.pos + data.len()].copy_from_slice(data);
        self.buf[self.pos + data.len()..end].fill(0);
        self.pos = end;
        Ok(())
    }
}

#[cfg(feature = "alloc")]
impl WireSink for Vec<u8> {
    fn write_aligned(&mut self, data: &[u8], wire_len: usize) -> Result<(), WireError> {
        if wire_len < data.len() {
            return Err(WireError::LengthOverflow);
        }
        self.extend_from_slice(data);
        let pad = wire_len - data.len();
        if pad > 0 {
            self.resize(self.len() + pad, 0);
        }
        Ok(())
    }
}

/// Little-endian Venus wire encoder writing into a [`WireSink`].
#[derive(Debug)]
pub struct Encoder<S> {
    sink: S,
}

impl<S: WireSink> Encoder<S> {
    #[must_use]
    pub const fn new(sink: S) -> Self {
        Self { sink }
    }

    #[must_use]
    pub fn into_inner(self) -> S {
        self.sink
    }

    #[must_use]
    pub const fn sink(&self) -> &S {
        &self.sink
    }

    pub fn write_u8(&mut self, v: u8) -> Result<(), WireError> {
        self.sink.write_aligned(&[v], 4)
    }

    pub fn write_i8(&mut self, v: i8) -> Result<(), WireError> {
        self.write_u8(v as u8)
    }

    pub fn write_u16(&mut self, v: u16) -> Result<(), WireError> {
        self.sink.write_aligned(&v.to_le_bytes(), 4)
    }

    pub fn write_i16(&mut self, v: i16) -> Result<(), WireError> {
        self.write_u16(v as u16)
    }

    pub fn write_u32(&mut self, v: u32) -> Result<(), WireError> {
        self.sink.write_aligned(&v.to_le_bytes(), 4)
    }

    pub fn write_i32(&mut self, v: i32) -> Result<(), WireError> {
        self.sink.write_aligned(&v.to_le_bytes(), 4)
    }

    pub fn write_u64(&mut self, v: u64) -> Result<(), WireError> {
        self.sink.write_aligned(&v.to_le_bytes(), 8)
    }

    pub fn write_i64(&mut self, v: i64) -> Result<(), WireError> {
        self.sink.write_aligned(&v.to_le_bytes(), 8)
    }

    pub fn write_f32(&mut self, v: f32) -> Result<(), WireError> {
        self.write_u32(v.to_bits())
    }

    pub fn write_f64(&mut self, v: f64) -> Result<(), WireError> {
        self.write_u64(v.to_bits())
    }

    pub fn write_bool32(&mut self, v: bool) -> Result<(), WireError> {
        self.write_u32(u32::from(v))
    }

    /// Encodes a wire `size_t` (always 64-bit `u64`).
    pub fn write_size_t(&mut self, v: u64) -> Result<(), WireError> {
        self.write_u64(v)
    }

    pub fn write_object_id(&mut self, id: ObjectId) -> Result<(), WireError> {
        self.write_u64(id.0)
    }

    pub fn write_array_size(&mut self, size: u64) -> Result<(), WireError> {
        self.write_u64(size)
    }

    pub fn write_simple_pointer(&mut self, non_null: bool) -> Result<(), WireError> {
        self.write_u64(u64::from(non_null))
    }

    pub fn write_blob(&mut self, data: &[u8]) -> Result<(), WireError> {
        let wire_len = align4(data.len()).ok_or(WireError::LengthOverflow)?;
        self.sink.write_aligned(data, wire_len)
    }

    /// Encodes `data` as a `len`-byte NUL-terminated C string (wire-padded to 4 bytes).
    /// `data` must not be empty; if it does not already end in `\0`, a trailing `\0` is written.
    pub fn write_cstr_bytes(&mut self, data: &[u8]) -> Result<(), WireError> {
        if data.is_empty() {
            return Err(WireError::InvalidString);
        }
        let wire_len = align4(data.len()).ok_or(WireError::LengthOverflow)?;
        self.sink.write_aligned(data, wire_len)
    }

    pub fn write_command_header(&mut self, header: CommandHeader) -> Result<(), WireError> {
        self.write_i32(header.cmd_type)?;
        self.write_u32(header.flags.0)
    }

    pub fn write_reply_header(&mut self, cmd_type: i32) -> Result<(), WireError> {
        self.write_i32(cmd_type)
    }

    pub fn write_u8_slice(&mut self, vals: &[u8]) -> Result<(), WireError> {
        self.write_blob(vals)
    }

    pub fn write_u16_slice(&mut self, vals: &[u16]) -> Result<(), WireError> {
        let byte_len = vals.len().checked_mul(2).ok_or(WireError::LengthOverflow)?;
        let wire_len = align4(byte_len).ok_or(WireError::LengthOverflow)?;
        for &v in vals {
            self.sink.write_aligned(&v.to_le_bytes(), 2)?;
        }
        let pad = wire_len - byte_len;
        if pad > 0 {
            self.sink.write_aligned(&[], pad)?;
        }
        Ok(())
    }

    pub fn write_u32_slice(&mut self, vals: &[u32]) -> Result<(), WireError> {
        for &v in vals {
            self.write_u32(v)?;
        }
        Ok(())
    }

    pub fn write_i32_slice(&mut self, vals: &[i32]) -> Result<(), WireError> {
        for &v in vals {
            self.write_i32(v)?;
        }
        Ok(())
    }

    pub fn write_u64_slice(&mut self, vals: &[u64]) -> Result<(), WireError> {
        for &v in vals {
            self.write_u64(v)?;
        }
        Ok(())
    }

    pub fn write_f32_slice(&mut self, vals: &[f32]) -> Result<(), WireError> {
        for &v in vals {
            self.write_f32(v)?;
        }
        Ok(())
    }

    pub fn write_object_id_slice(&mut self, vals: &[ObjectId]) -> Result<(), WireError> {
        for &v in vals {
            self.write_object_id(v)?;
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn scalar_round_trips_and_sub_4byte_padding() {
        let mut buf = [0xAAu8; 128];
        let mut enc = Encoder::new(SliceSink::new(&mut buf));
        enc.write_u8(0x7F).unwrap();
        enc.write_i8(-5).unwrap();
        enc.write_u16(0x1234).unwrap();
        enc.write_i16(-1234).unwrap();
        enc.write_u32(0xDEAD_BEEF).unwrap();
        enc.write_i32(-42).unwrap();
        enc.write_u64(0x0123_4567_89AB_CDEF).unwrap();
        enc.write_i64(-999_999_999_999).unwrap();
        enc.write_f32(3.5).unwrap();
        enc.write_f64(-1.25).unwrap();
        enc.write_bool32(true).unwrap();
        enc.write_size_t(4096).unwrap();
        enc.write_object_id(ObjectId(77)).unwrap();

        let written = enc.into_inner().written();
        assert_eq!(written, 4 * 6 + 8 * 2 + 4 + 8 + 4 + 8 + 8);

        // Verify sub-4-byte scalars zero-pad upper bytes.
        assert_eq!(&buf[0..4], &[0x7F, 0, 0, 0]);
        assert_eq!(&buf[8..12], &[0x34, 0x12, 0, 0]);

        let mut dec = Decoder::new(&buf[..written]);
        assert_eq!(dec.read_u8().unwrap(), 0x7F);
        assert_eq!(dec.read_i8().unwrap(), -5);
        assert_eq!(dec.read_u16().unwrap(), 0x1234);
        assert_eq!(dec.read_i16().unwrap(), -1234);
        assert_eq!(dec.read_u32().unwrap(), 0xDEAD_BEEF);
        assert_eq!(dec.read_i32().unwrap(), -42);
        assert_eq!(dec.read_u64().unwrap(), 0x0123_4567_89AB_CDEF);
        assert_eq!(dec.read_i64().unwrap(), -999_999_999_999);
        assert_eq!(dec.read_f32().unwrap(), 3.5);
        assert_eq!(dec.read_f64().unwrap(), -1.25);
        assert!(dec.read_bool32().unwrap());
        assert_eq!(dec.read_size_t().unwrap(), 4096);
        assert_eq!(dec.read_object_id().unwrap(), ObjectId(77));
        assert!(dec.is_empty());
    }

    #[test]
    fn blob_and_cstr_padding() {
        for len in [1usize, 2, 3, 4, 5, 8] {
            let payload: Vec<u8> = (1..=len).map(|i| b'a' + (i as u8 - 1)).collect();
            let mut enc = Encoder::new(Vec::new());
            enc.write_blob(&payload).unwrap();
            let wire = enc.into_inner();
            assert_eq!(wire.len(), align4(len).unwrap());
            assert_eq!(&wire[..len], payload.as_slice());
            assert!(wire[len..].iter().all(|&b| b == 0));

            let mut dec = Decoder::new(&wire);
            assert_eq!(dec.read_blob(len).unwrap(), payload.as_slice());
            assert!(dec.is_empty());
        }

        let mut dec_empty = Decoder::new(&[0, 0, 0, 0]);
        assert_eq!(dec_empty.read_cstr_bytes(0), Err(WireError::InvalidString));

        let mut enc_str = Encoder::new(Vec::new());
        enc_str.write_cstr_bytes(b"hello\0").unwrap();
        let wire_str = enc_str.into_inner();
        assert_eq!(wire_str.len(), 8);
        let mut dec_str = Decoder::new(&wire_str);
        assert_eq!(dec_str.read_string(6).unwrap(), "hello");
        assert!(dec_str.is_empty());
    }

    #[test]
    fn scalar_arrays_odd_counts() {
        let mut enc = Encoder::new(Vec::new());
        enc.write_u8_slice(&[1, 2, 3]).unwrap();
        enc.write_u16_slice(&[10, 20, 30]).unwrap();
        enc.write_u32_slice(&[100, 200]).unwrap();
        enc.write_i32_slice(&[-1, 2, -3]).unwrap();
        enc.write_u64_slice(&[9, 8]).unwrap();
        enc.write_f32_slice(&[1.0, 2.5]).unwrap();
        enc.write_object_id_slice(&[ObjectId(1), ObjectId(2)]).unwrap();
        let wire = enc.into_inner();

        let expected_len = 4 + 8 + 8 + 12 + 16 + 8 + 16;
        assert_eq!(wire.len(), expected_len);

        let mut dec = Decoder::new(&wire);
        assert_eq!(dec.read_u8_slice(3).unwrap(), &[1, 2, 3]);
        assert_eq!(dec.read_u16_vec(3).unwrap(), vec![10, 20, 30]);
        assert_eq!(dec.read_u32_vec(2).unwrap(), vec![100, 200]);
        assert_eq!(dec.read_i32_vec(3).unwrap(), vec![-1, 2, -3]);
        assert_eq!(dec.read_u64_vec(2).unwrap(), vec![9, 8]);
        assert_eq!(dec.read_f32_vec(2).unwrap(), vec![1.0, 2.5]);
        assert_eq!(
            dec.read_object_id_vec(2).unwrap(),
            vec![ObjectId(1), ObjectId(2)]
        );
        assert!(dec.is_empty());
    }

    #[test]
    fn array_size_pointer_and_headers() {
        let mut enc = Encoder::new(Vec::new());
        enc.write_command_header(CommandHeader {
            cmd_type: 17,
            flags: CommandFlags::generate_reply(),
        })
        .unwrap();
        enc.write_reply_header(17).unwrap();
        enc.write_array_size(4).unwrap();
        enc.write_simple_pointer(false).unwrap();
        enc.write_simple_pointer(true).unwrap();
        enc.write_u64(2).unwrap();
        let wire = enc.into_inner();

        let mut dec = Decoder::new(&wire);
        assert_eq!(dec.peek_i32().unwrap(), 17);
        let hdr = dec.read_command_header().unwrap();
        assert_eq!(hdr.cmd_type, 17);
        assert!(hdr.flags.wants_reply());
        assert_eq!(dec.read_reply_header().unwrap(), 17);
        assert_eq!(dec.read_array_size(4).unwrap(), 4);
        assert!(!dec.read_simple_pointer().unwrap());
        assert!(dec.read_simple_pointer().unwrap());
        assert_eq!(
            dec.read_simple_pointer(),
            Err(WireError::InvalidPointerFlag(2))
        );

        let mut dec_bad_arr = Decoder::new(&wire[12..20]);
        assert_eq!(
            dec_bad_arr.read_array_size(5),
            Err(WireError::InvalidArraySize {
                expected: 5,
                actual: 4
            })
        );
    }

    #[test]
    fn bounds_and_overflow_errors() {
        let mut small = [0u8; 3];
        let mut enc = Encoder::new(SliceSink::new(&mut small));
        assert_eq!(enc.write_u32(1), Err(WireError::BufferTooSmall));

        let mut dec = Decoder::new(&[1, 2]);
        assert_eq!(dec.read_u32(), Err(WireError::UnexpectedEof));
        assert_eq!(align4(usize::MAX), None);
        assert_eq!(dec.read_blob(usize::MAX), Err(WireError::LengthOverflow));
    }
}
