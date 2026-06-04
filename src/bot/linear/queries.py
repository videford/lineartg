"""GraphQL documents for the Linear API.

Mutations that surface end users (createAsUser / displayIconUrl) let a
seat-less Telegram member appear as the actor in Linear's history while the
work is performed by the OAuth application (actor=app).
"""

VIEWER = """
query Viewer {
  viewer { id name }
  organization { id name }
}
"""

TEAMS = """
query Teams {
  teams(first: 50) {
    nodes { id name key }
  }
}
"""

PROJECTS = """
query Projects($teamId: String!) {
  team(id: $teamId) {
    projects(first: 100) {
      nodes { id name state }
    }
  }
}
"""

ALL_PROJECTS = """
query AllProjects {
  projects(first: 250) {
    nodes {
      id
      name
      state
      teams(first: 1) { nodes { id } }
    }
  }
}
"""

WORKFLOW_STATES = """
query WorkflowStates($teamId: String!) {
  team(id: $teamId) {
    states(first: 50) {
      nodes { id name type position }
    }
  }
}
"""

# Find or create the "tg:<name>" label used to represent a seat-less assignee.
LABELS = """
query Labels($teamId: String!) {
  team(id: $teamId) {
    labels(first: 250) {
      nodes { id name }
    }
  }
}
"""

LABEL_CREATE = """
mutation LabelCreate($name: String!, $teamId: String!) {
  issueLabelCreate(input: { name: $name, teamId: $teamId }) {
    success
    issueLabel { id name }
  }
}
"""

ISSUE_CREATE = """
mutation IssueCreate($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue { id identifier title url }
  }
}
"""

ISSUE_DETAIL = """
query IssueDetail($id: String!) {
  issue(id: $id) {
    id
    identifier
    title
    description
    url
    priority
    priorityLabel
    dueDate
    estimate
    state { id name type }
    project { id name }
    team { id }
    assignee { name }
    labels(first: 50) { nodes { id name } }
    comments(last: 3) {
      nodes { body user { name } botActor { userDisplayName } createdAt }
    }
  }
}
"""

ISSUE_UPDATE = """
mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue { id identifier state { name } }
  }
}
"""

COMMENT_CREATE = """
mutation CommentCreate($input: CommentCreateInput!) {
  commentCreate(input: $input) {
    success
    comment { id url }
  }
}
"""

ISSUES_BY_PROJECT = """
query IssuesByProject($projectId: String!) {
  project(id: $projectId) {
    issues(first: 40, orderBy: updatedAt) {
      nodes {
        id
        identifier
        title
        url
        priority
        priorityLabel
        state { name type }
        project { name }
      }
    }
  }
}
"""

ISSUE_SEARCH = """
query IssueSearch($term: String!) {
  issues(
    filter: { title: { containsIgnoreCase: $term } }
    first: 20
    orderBy: updatedAt
  ) {
    nodes {
      id
      identifier
      title
      url
      priority
      priorityLabel
      state { name type }
      project { name }
    }
  }
}
"""

# Issues carrying a given label — backs the /my command for seat-less members.
ISSUES_BY_LABEL = """
query IssuesByLabel($label: String!) {
  issues(
    filter: { labels: { name: { eq: $label } } }
    first: 50
    orderBy: updatedAt
  ) {
    nodes {
      id
      identifier
      title
      url
      priority
      priorityLabel
      state { name type }
      project { name }
    }
  }
}
"""
