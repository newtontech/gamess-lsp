/**
 * Tests for GAMESS Input File Parser
 */

import {
  parseGamessInput,
  validateGamessInput,
  ControlGroup,
  BasisGroup,
  DataGroup,
  GamessInput
} from '../../src/parsers/inp';

describe('GAMESS Input Parser', () => {

  describe('parseGamessInput', () => {

    it('should parse water molecule with C1 symmetry', () => {
      const input = `
 $CONTRL SCFTYP=RHF RUNTYP=OPTIMIZE $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
Water molecule
C1
O 8 0.000000  0.000000  0.117300
H 1 0.000000  0.756950 -0.469200
H 1 0.000000 -0.756950 -0.469200
 $END
      `.trim();

      const result: GamessInput = parseGamessInput(input);

      // Check $CONTRL group
      expect(result.contrl).toBeDefined();
      expect(result.contrl!.scftyp).toBe('RHF');
      expect(result.contrl!.runtyp).toBe('OPTIMIZE');

      // Check $BASIS group
      expect(result.basis).toBeDefined();
      expect(result.basis!.gbasis).toBe('STO');
      expect(result.basis!.ngauss).toBe(3);

      // Check $DATA group
      expect(result.data).toBeDefined();
      expect(result.data!.title).toBe('Water molecule');
      expect(result.data!.symmetry).toBe('C1');
      expect(result.data!.atoms).toHaveLength(3);

      // Check oxygen atom
      expect(result.data!.atoms[0]).toEqual({
        symbol: 'O',
        atomicNumber: 8,
        x: 0.0,
        y: 0.0,
        z: 0.117300,
      });

      // Check hydrogen atoms
      expect(result.data!.atoms[1]).toEqual({
        symbol: 'H',
        atomicNumber: 1,
        x: 0.0,
        y: 0.756950,
        z: -0.469200,
      });

      expect(result.data!.atoms[2]).toEqual({
        symbol: 'H',
        atomicNumber: 1,
        x: 0.0,
        y: -0.756950,
        z: -0.469200,
      });
    });

    it('should parse $CONTRL group with only SCFTYP', () => {
      const input = `
 $CONTRL SCFTYP=UHF $END
 $DATA
Test
C1
H 1 0.0 0.0 0.0
 $END
      `.trim();

      const result = parseGamessInput(input);
      expect(result.contrl).toEqual({
        scftyp: 'UHF',
        runtyp: undefined,
      });
    });

    it('should parse $BASIS group without NGAUSS', () => {
      const input = `
 $CONTRL SCFTYP=RHF $END
 $BASIS GBASIS=PM3 $END
 $DATA
Test
C1
H 1 0.0 0.0 0.0
 $END
      `.trim();

      const result = parseGamessInput(input);
      expect(result.basis).toEqual({
        gbasis: 'PM3',
        ngauss: undefined,
      });
    });

    it('should handle missing groups gracefully', () => {
      const input = `
 $CONTRL SCFTYP=RHF $END
      `.trim();

      const result = parseGamessInput(input);
      expect(result.contrl).toBeDefined();
      expect(result.basis).toBeUndefined();
      expect(result.data).toBeUndefined();
    });

    it('should parse case-insensitive group names', () => {
      const input = `
 $contrl scftyp=rhf $end
 $basis gbasis=sto ngauss=3 $end
 $data
Water
C1
O 8 0.0 0.0 0.0
 $end
      `.trim();

      const result = parseGamessInput(input);
      expect(result.contrl).toBeDefined();
      expect(result.contrl!.scftyp).toBe('rhf');
      expect(result.basis).toBeDefined();
      expect(result.data).toBeDefined();
    });

    it('should handle empty input', () => {
      const result = parseGamessInput('');
      expect(result).toEqual({});
    });

    it('should parse multiple spaces between key-value pairs', () => {
      const input = `
 $CONTRL   SCFTYP=RHF    RUNTYP=ENERGY   $END
 $DATA
Test
C1
H 1 0.0 0.0 0.0
 $END
      `.trim();

      const result = parseGamessInput(input);
      expect(result.contrl!.scftyp).toBe('RHF');
      expect(result.contrl!.runtyp).toBe('ENERGY');
    });
  });

  describe('validateGamessInput', () => {

    it('should return no errors for valid water input', () => {
      const input = `
 $CONTRL SCFTYP=RHF $END
 $DATA
Water
C1
O 8 0.0 0.0 0.0
 $END
      `.trim();

      const errors = validateGamessInput(input);
      expect(errors).toHaveLength(0);
    });

    it('should report missing $CONTRL group', () => {
      const input = `
 $DATA
Test
C1
H 1 0.0 0.0 0.0
 $END
      `.trim();

      const errors = validateGamessInput(input);
      expect(errors).toContain('Missing required $CONTRL group');
    });

    it('should report missing $DATA group', () => {
      const input = `
 $CONTRL SCFTYP=RHF $END
      `.trim();

      const errors = validateGamessInput(input);
      expect(errors).toContain('Missing required $DATA group');
    });

    it('should report missing SCFTYP', () => {
      const input = `
 $CONTRL RUNTYP=OPTIMIZE $END
 $DATA
Test
C1
H 1 0.0 0.0 0.0
 $END
      `.trim();

      const errors = validateGamessInput(input);
      expect(errors).toContain('SCFTYP not specified in $CONTRL group');
    });

    it('should report no atoms in $DATA group', () => {
      const input = `
 $CONTRL SCFTYP=RHF $END
 $DATA
Test
C1
 $END
      `.trim();

      const errors = validateGamessInput(input);
      expect(errors).toContain('No atoms found in $DATA group');
    });
  });
});
