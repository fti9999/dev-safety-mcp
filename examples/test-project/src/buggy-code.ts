// File with intentional issues for testing validation
import { User } from './user-service';

// TypeScript error: missing return type annotation
export function processUser(user) {
  // Syntax error: missing semicolon (if linting is strict)
  const processedUser = {
    ...user,
    processedAt: new Date()
  }
  
  // Logic issue: no return statement but function should return something
  console.log('Processing user:', processedUser);
}

// Missing interface definition
export function createUserFromData(data: any): User {
  // Type error: property names don't match User interface exactly
  return {
    userId: data.id,  // Wrong property name
    fullName: data.name,  // Wrong property name  
    emailAddress: data.email  // Wrong property name
  };
}

// Unused variable (linting issue)
const unusedVariable = "This will trigger a linting warning";

// Missing export for a function that should be exported
function helperFunction() {
  return "helper";
}
