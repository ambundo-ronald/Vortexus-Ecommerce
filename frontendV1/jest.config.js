export default {
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["@testing-library/jest-dom"],
  moduleNameMapper: {
    "\\.(css|scss)$": "<rootDir>/tests/__mocks__/styleMock.js"
  },
  transform: {
    "^.+\\.[jt]sx?$": "babel-jest"
  }
};
