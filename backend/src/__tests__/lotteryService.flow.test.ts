import * as svc from '../services/lotteryService.js';

// Mock DB models and queue
jest.mock('../../models/Submission', () => ({ SubmissionModel: { countDocuments: jest.fn(), create: jest.fn() } }));
jest.mock('../../models/UserMeta', () => ({ UserMetaModel: { findOne: jest.fn(), create: jest.fn() } }));
jest.mock('../queue/notificationQueue', () => ({ enqueueNotification: jest.fn() }));

describe('handleSubmissionAndLottery', () => {
  const { SubmissionModel } = require('../../models/Submission');
  const { UserMetaModel } = require('../../models/UserMeta');

  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
  });

  it('returns none when already submitted today', async () => {
    SubmissionModel.countDocuments.mockResolvedValue(1);
    const res = await svc.handleSubmissionAndLottery({ submitterAnonId: 'a', aim: 'x', steps: ['1','2','3'], frameType: 'f' });
    expect(res.jpResult).toBe('none');
  });

  it('win path resets bonusCount and enqueues notification', async () => {
    SubmissionModel.countDocuments.mockResolvedValue(0);
    SubmissionModel.create.mockResolvedValue({ save: jest.fn() });
    const save = jest.fn();
    UserMetaModel.findOne.mockResolvedValue({ anonId: 'a', lotteryBonusCount: 10, cardsAlbum: [], save });

    // Force win
    jest.spyOn(Math, 'random').mockReturnValue(0); // always < p

    const res = await svc.handleSubmissionAndLottery({ submitterAnonId: 'a', aim: 'x', steps: ['1','2','3'], frameType: 'f' });
    expect(res.jpResult).toBe('win');
    expect(res.bonusCount).toBe(0);
  });

  it('lose path increments bonusCount', async () => {
    SubmissionModel.countDocuments.mockResolvedValue(0);
    SubmissionModel.create.mockResolvedValue({ save: jest.fn() });
    const save = jest.fn();
    UserMetaModel.findOne.mockResolvedValue({ anonId: 'a', lotteryBonusCount: 1, cardsAlbum: [], save });

    // Force lose
    jest.spyOn(Math, 'random').mockReturnValue(1); // always >= p

    const res = await svc.handleSubmissionAndLottery({ submitterAnonId: 'a', aim: 'x', steps: ['1','2','3'], frameType: 'f' });
    expect(res.jpResult).toBe('lose');
    expect(res.bonusCount).toBe(2);
  });
});
