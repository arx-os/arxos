/**
 * Auth Service - Handles authentication for AR functionality
 */

import { Logger } from '../utils/Logger';

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

export class AuthService {
  private logger: Logger;
  private currentUser: User | null = null;

  constructor() {
    this.logger = new Logger('AuthService');
  }

  getCurrentUser(): User | null {
    return this.currentUser;
  }

  setCurrentUser(user: User): void {
    this.currentUser = user;
  }

  isAuthenticated(): boolean {
    return this.currentUser !== null;
  }

  logout(): void {
    this.currentUser = null;
  }
}