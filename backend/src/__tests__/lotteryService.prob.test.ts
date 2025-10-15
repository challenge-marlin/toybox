import { calculateFinalProbability } from '../services/lotteryService.js';

describe('calculateFinalProbability', () => {
  it('k=0 -> 0.008', () => {
    expect(calculateFinalProbability(0)).toBeCloseTo(0.008, 6);
  });
  it('k=1 -> 0.010', () => {
    expect(calculateFinalProbability(1)).toBeCloseTo(0.010, 6);
  });
  it('k=10 caps at 0.05', () => {
    expect(calculateFinalProbability(10)).toBeCloseTo(0.05, 6);
  });
  it('negative k treated as 0', () => {
    expect(calculateFinalProbability(-5)).toBeCloseTo(0.008, 6);
  });
});
