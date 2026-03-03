# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-03-03

### Added
- Initial release of GAMESS-LSP
- Complete LSP server implementation with pygls
- Parser for GAMESS input files (.inp)
- Support for 18 GAMESS $GROUPs with 100+ parameters
- Auto-completion for groups, parameters, and values
- Hover documentation for groups and parameters
- Real-time diagnostics and validation
- Document symbol provider (outline view)
- Folding range provider for $GROUP sections
- 12 code snippets for common calculations
- CLI with validate and parse commands
- 113 unit tests with comprehensive coverage
- 6 example input files
- CI/CD pipeline with GitHub Actions
- Support for Python 3.8-3.12

### GAMESS Groups Supported
- $CONTRL - Control options
- $BASIS - Basis set specification
- $SYSTEM - System resources
- $SCF - SCF convergence options
- $DFT - Density Functional Theory
- $CIS - Configuration Interaction Singles
- $FORCE - Force constant calculation
- $HESS - Hessian matrix options
- $MP2 - MP2 perturbation theory
- $CC - Coupled Cluster
- $EOM - Equation of Motion
- $PCM - Polarizable Continuum Model
- $COSMO - Conductor-like Screening Model
- $STATPT - Geometry optimization
- $GUESS - Initial guess options
- $POP - Population analysis
- $ELMOM - Electric moments
- $LOCAL - Localized orbitals

[0.1.0]: https://github.com/newtontech/gamess-lsp/releases/tag/v0.1.0
