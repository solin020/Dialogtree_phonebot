use pyo3::prelude::*;
use std::borrow::Cow;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn pcms16le_to_mulaw<'a>(a: Vec<u8>) -> PyResult<Cow<'a, [u8]>> {
    let mut retval: Vec<u8> = vec![0;a.len() / 4];
    for (pos, i) in a.chunks_exact(4).into_iter().enumerate(){
        let val = (i16::from_le_bytes([i[0], i[1]])) >> 2;
        match val {
            4063..=i16::MAX => {
                retval[pos] = (((8158-val) / 256) + 0x80).try_into()?;
            }
            2015..=4062 => {
                retval[pos] = (((4062-val) / 128) + 0x90).try_into()?;
            }
            991..=2014 => {
                retval[pos] = (((2014-val) / 64) + 0xA0).try_into()?;
            }
            479..=990 => {
                retval[pos] = (((990-val) / 32) + 0xB0).try_into()?;
            }
            223..=478 => {
                retval[pos] = (((478-val) / 16) + 0xC0).try_into()?;
            }
            95..=222 => {
                retval[pos] = (((222-val) / 8) + 0xD0).try_into()?;
            }
            31..=94 => {
                retval[pos] = (((94-val) / 4) + 0xE0).try_into()?;
            }
            1..=30 => {
                retval[pos] = (((30-val) / 2) + 0xF0).try_into()?;
            }
            0 => retval[pos] = 0xFF,
            -1 => retval[pos] = 0x7F,
            -31..=-2 => {
                retval[pos] = (((val+31) / 2) + 0x70).try_into()?;
            }
            -95..=-32 => {
                retval[pos] = (((val+95) / 4) + 0x60).try_into()?;
            }
            -223..=-96 => {
                retval[pos] = (((val+223) / 8) + 0x50).try_into()?;
            }
            -479..=-224 => {
                retval[pos] = (((val+479) / 16) + 0x40).try_into()?;
            }
            -991..=-480 => {
                retval[pos] = (((val+991) / 32) + 0x30).try_into()?;
            }
            -2015..=-992 => {
                retval[pos] = (((val+2015) / 64) + 0x20).try_into()?;
            }
            -4063..=-2016 => {
                retval[pos] = (((val+4063) / 128) + 0x10).try_into()?;
            }
            i16::MIN..=-4064 => {
                retval[pos] = ((val+8159) / 256).try_into()?;
            }
        }
    }
    Ok(Cow::Owned(retval))
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn mulaw(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(pcms16le_to_mulaw, m)?)?;
    Ok(())
}
