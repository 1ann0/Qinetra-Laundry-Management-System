// Same-browser logout carries account scope only, never authentication secrets.
export function makeLogoutEvent(apiUrl, userId) {
  return {action: "logout", apiUrl, userId};
}

export function appliesToSession(message, session) {
  return Boolean(message?.action === "logout" && Number.isInteger(message.userId) && message.userId > 0 &&
    message.userId === session.userId && message.apiUrl === session.apiUrl);
}
