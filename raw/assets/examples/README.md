# GAMESS Input File Examples

This directory contains example GAMESS input files for various calculation types.

## Files

### water_dft.inp
Geometry optimization of water molecule using B3LYP DFT functional.
- **Method**: RHF/B3LYP
- **Basis**: 6-31G(d)
- **Calculation**: Geometry optimization

### h2o_freq.inp
Vibrational frequency calculation for water.
- **Method**: RHF
- **Basis**: CC-PVDZ
- **Calculation**: Hessian and frequency analysis

### tddft_excited.inp
TDDFT excited state calculation for formaldehyde.
- **Method**: TDDFT/B3LYP
- **Basis**: CC-PVTZ
- **Calculation**: 5 excited states

### irc_reaction.inp
IRC (Intrinsic Reaction Coordinate) calculation template.
- **Method**: RHF
- **Basis**: CC-PVDZ
- **Calculation**: Reaction path following

### mp2_energy.inp
MP2 single point energy calculation template.
- **Method**: MP2
- **Basis**: CC-PVTZ
- **Calculation**: Single point energy

## Usage

To run these examples with GAMESS:

```bash
rungms input_file.inp > output.log
```

## References

- [GAMESS Documentation](https://www.msg.chem.iastate.edu/gamess/documentation.html)
- [GAMESS Input Manual](https://www.msg.chem.iastate.edu/gamess/GAMESS_Manual/input.pdf)
