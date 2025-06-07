// Unit tests for UserService
import { UserService, validateEmail, User } from '../src/user-service';

describe('UserService', () => {
  let userService: UserService;

  beforeEach(() => {
    userService = new UserService();
  });

  test('should add a user', () => {
    const user: User = { id: 1, name: 'John Doe', email: 'john@example.com' };
    userService.addUser(user);
    
    const foundUser = userService.findUser(1);
    expect(foundUser).toEqual(user);
  });

  test('should find an existing user', () => {
    const user: User = { id: 1, name: 'Jane Doe', email: 'jane@example.com' };
    userService.addUser(user);
    
    const foundUser = userService.findUser(1);
    expect(foundUser).toBeDefined();
    expect(foundUser?.name).toBe('Jane Doe');
  });

  test('should return undefined for non-existent user', () => {
    const foundUser = userService.findUser(999);
    expect(foundUser).toBeUndefined();
  });

  test('should return all users', () => {
    const user1: User = { id: 1, name: 'User 1', email: 'user1@example.com' };
    const user2: User = { id: 2, name: 'User 2', email: 'user2@example.com' };
    
    userService.addUser(user1);
    userService.addUser(user2);
    
    const allUsers = userService.getAllUsers();
    expect(allUsers).toHaveLength(2);
    expect(allUsers).toContain(user1);
    expect(allUsers).toContain(user2);
  });
});

describe('validateEmail', () => {
  test('should validate correct email formats', () => {
    expect(validateEmail('test@example.com')).toBe(true);
    expect(validateEmail('user.name@domain.org')).toBe(true);
    expect(validateEmail('user+tag@example.co.uk')).toBe(true);
  });

  test('should reject invalid email formats', () => {
    expect(validateEmail('invalid-email')).toBe(false);
    expect(validateEmail('missing@domain')).toBe(false);
    expect(validateEmail('@missing-local.com')).toBe(false);
    expect(validateEmail('spaces in@email.com')).toBe(false);
  });

  test('should handle edge cases', () => {
    expect(validateEmail('')).toBe(false);
    expect(validateEmail('   ')).toBe(false);
  });
});
