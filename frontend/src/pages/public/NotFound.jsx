import { Link } from 'react-router-dom'
import Button from '../../components/Button'
import styles from './NotFound.module.css'

export default function NotFound() {
  return (
    <div className={styles.page}>
      <div className={styles.code}>404</div>
      <h1 className={styles.title}>Page not found</h1>
      <p className={styles.text}>The page you’re looking for doesn’t exist or has moved.</p>
      <Link to="/"><Button>Back to home</Button></Link>
    </div>
  )
}
