#!/usr/bin/env node
/**
 * CRITICAL: API URL Validation Script
 *
 * This script prevents broken API calls from being deployed.
 * The trailing slash issue caused a production outage - NEVER AGAIN.
 *
 * Run: node scripts/validate-api-urls.js
 */

const fs = require('fs')
const path = require('path')

const FRONTEND_ROOT = path.resolve(__dirname, '..')

// Recursively get all TypeScript/TSX files
function getAllTsFiles(dir) {
  const files = []
  const entries = fs.readdirSync(dir, { withFileTypes: true })

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory() && !entry.name.includes('node_modules') && entry.name !== 'dist' && entry.name !== 'scripts') {
      files.push(...getAllTsFiles(fullPath))
    } else if (entry.isFile() && (entry.name.endsWith('.ts') || entry.name.endsWith('.tsx'))) {
      files.push(fullPath)
    }
  }
  return files
}

function main() {
  const violations = []
  const tsFiles = getAllTsFiles(path.join(FRONTEND_ROOT, 'app'))

  console.log('========================================')
  console.log('API URL Validation')
  console.log('========================================\n')
  console.log(`Scanning ${tsFiles.length} files...\n`)

  for (const file of tsFiles) {
    const content = fs.readFileSync(file, 'utf-8')
    const lines = content.split('\n')
    const relPath = path.relative(FRONTEND_ROOT, file)

    lines.forEach((line, index) => {
      // Check for trailing slash before ?
      // Pattern: api.get('cards/?' or api.get("cards/?" or api.get(`cards/?
      if (/api\.(get|post|put|delete|patch)\s*\([`'"][^`'"]*\/\?/.test(line)) {
        violations.push({
          file: relPath,
          line: index + 1,
          content: line.trim(),
          type: 'TRAILING_SLASH'
        })
      }

      // Check for hardcoded localhost (skip comments, test files, and env fallbacks)
      if (!line.trim().startsWith('//') && !file.includes('.test.')) {
        if (line.includes('localhost:8000') || line.includes('127.0.0.1:8000')) {
          // Allow localhost as fallback: `env.VAR || 'http://localhost...'`
          const isFallback = /\|\|\s*['"`]http:\/\/(localhost|127\.0\.0\.1):8000/.test(line)

          // Also allow localhost in getApiUrl() functions (dev fallback pattern)
          // Check surrounding lines for context indicating it's a fallback
          const prevLine = index > 0 ? lines[index - 1].toLowerCase() : ''
          const isDevFallback = prevLine.includes('local') || prevLine.includes('dev') || prevLine.includes('fallback')

          if (!isFallback && !isDevFallback) {
            violations.push({
              file: relPath,
              line: index + 1,
              content: line.trim(),
              type: 'HARDCODED_LOCALHOST'
            })
          }
        }
      }
    })
  }

  if (violations.length > 0) {
    console.log('\n========================================')
    console.log('CRITICAL VIOLATIONS FOUND!')
    console.log('========================================\n')

    for (const v of violations) {
      console.log(`[${v.type}] ${v.file}:${v.line}`)
      console.log(`  ${v.content}\n`)
    }

    console.log('========================================')
    console.log('FIX REQUIRED:')
    console.log('  - Trailing slash: api.get("cards/?x=1") -> api.get("cards?x=1")')
    console.log('  - Localhost: Use relative URLs or env variables')
    console.log('========================================\n')

    process.exit(1)
  } else {
    console.log('All API URL checks passed!')
    process.exit(0)
  }
}

main()
