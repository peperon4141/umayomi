export default {
  rules: {
    'single-line-if': {
      meta: {
        type: 'layout',
        fixable: 'code',
        messages: {
          singleLine: '1行しか含まないif文は1行で実装してください'
        }
      },
      create(context) {
        const sourceCode = context.sourceCode

        return {
          IfStatement(node) {
            // 既に1行になっている場合はスキップ
            const nodeText = sourceCode.getText(node)
            if (!nodeText.includes('\n')) {
              return
            }

            const consequent = node.consequent
            let statement = null

            // BlockStatementで、1つの文のみを含む場合
            if (
              consequent.type === 'BlockStatement' &&
              consequent.body.length === 1
            ) {
              statement = consequent.body[0]
            } else if (consequent.type !== 'BlockStatement') {
              // BlockStatementでない場合（直接文が書かれている場合）
              statement = consequent
            }

            // elseがある場合、elseの文をチェック
            let elseStatement = null
            let elseStatementText = ''
            if (node.alternate) {
              if (node.alternate.type === 'BlockStatement' && node.alternate.body.length === 1) {
                elseStatement = node.alternate.body[0]
              } else if (node.alternate.type !== 'BlockStatement') {
                elseStatement = node.alternate
              }

              if (elseStatement) {
                elseStatementText = sourceCode.getText(elseStatement)
                // elseの文が複数行にわたっている場合はスキップ
                if (elseStatementText.includes('\n')) {
                  return
                }
                // elseの文が対応する文タイプでない場合はスキップ
                if (
                  elseStatement.type !== 'ReturnStatement' &&
                  elseStatement.type !== 'ContinueStatement' &&
                  elseStatement.type !== 'BreakStatement' &&
                  elseStatement.type !== 'ThrowStatement' &&
                  elseStatement.type !== 'ExpressionStatement' &&
                  elseStatement.type !== 'IfStatement'
                ) {
                  return
                }
              }
            }

            // return文、continue文、break文、throw文、式文など
            // 文が複数行にわたっている場合は1行にまとめない
            if (
              statement &&
              (statement.type === 'ReturnStatement' ||
                statement.type === 'ContinueStatement' ||
                statement.type === 'BreakStatement' ||
                statement.type === 'ThrowStatement' ||
                statement.type === 'ExpressionStatement')
            ) {
              const statementText = sourceCode.getText(statement)
              // 文が複数行にわたっている場合はスキップ
              if (statementText.includes('\n')) {
                return
              }

              // elseがある場合はスキップ（構文エラーを避けるため）
              if (node.alternate) {
                return
              }

              context.report({
                node,
                messageId: 'singleLine',
                fix(fixer) {
                  const testText = sourceCode.getText(node.test)

                  return fixer.replaceText(
                    node,
                    `if (${testText}) ${statementText}`
                  )
                }
              })
            } else if (node.alternate && elseStatement) {
              // elseが含まれている場合はスキップ（構文エラーを避けるため）
              return
            }
          }
        }
      }
    },

    'single-line-arrow': {
      meta: {
        type: 'layout',
        fixable: 'code',
        messages: {
          singleLine: '1行しか含まないアロー関数は1行で実装してください'
        }
      },
      create(context) {
        const sourceCode = context.sourceCode

        return {
          ArrowFunctionExpression(node) {
            // 既に1行になっている場合はスキップ（ブロック本体でない場合）
            if (node.body.type !== 'BlockStatement') {
              return
            }

            // ブロック本体で、1つの文のみを含む場合
            if (node.body.body.length === 1) {
              const statement = node.body.body[0]

              // return文のみの場合
              if (statement.type === 'ReturnStatement') {
                context.report({
                  node,
                  messageId: 'singleLine',
                  fix(fixer) {
                    if (!node.params || node.params.length === 0 || !statement.argument) {
                      return null
                    }
                    const paramsText = node.params.map((param) => sourceCode.getText(param)).join(', ')
                    const returnValueText = sourceCode.getText(statement.argument)
                    const asyncText = node.async ? 'async ' : ''

                    return fixer.replaceText(
                      node,
                      `${asyncText}(${paramsText}) => ${returnValueText}`
                    )
                  }
                })
              }
            }
          }
        }
      }
    },

    'single-line-case': {
      meta: {
        type: 'layout',
        fixable: 'code',
        messages: {
          singleLine: '1行しか含まないcase文は1行で実装してください'
        }
      },
      create(context) {
        const sourceCode = context.sourceCode

        return {
          SwitchCase(node) {
            // 既に1行になっている場合はスキップ
            const nodeText = sourceCode.getText(node)
            if (!nodeText.includes('\n')) {
              return
            }

            // 1つの文のみを含む場合（break文を除く）
            const statements = node.consequent.filter(
              (stmt) => stmt.type !== 'BreakStatement'
            )

            if (statements.length === 1) {
              const statement = statements[0]

              // return文、continue文、throw文、式文など
              if (
                statement.type === 'ReturnStatement' ||
                statement.type === 'ContinueStatement' ||
                statement.type === 'ThrowStatement' ||
                statement.type === 'ExpressionStatement'
              ) {
                context.report({
                  node,
                  messageId: 'singleLine',
                  fix(fixer) {
                    const caseLabel = node.test
                      ? `case ${sourceCode.getText(node.test)}`
                      : 'default'
                    const statementText = sourceCode.getText(statement)
                    const breakText = node.consequent.some(
                      (stmt) => stmt.type === 'BreakStatement'
                    )
                      ? ' break'
                      : ''

                    return fixer.replaceText(
                      node,
                      `${caseLabel}: ${statementText}${breakText}`
                    )
                  }
                })
              }
            }
          }
        }
      }
    }
  }
}

