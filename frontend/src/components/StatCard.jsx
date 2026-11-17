import Card from './Card'
import Icon from './Icon'
import styles from './StatCard.module.css'

export default function StatCard({ label, value, icon, tone = 'navy', hint }) {
  return (
    <Card className={styles.card} padded={false}>
      <div className={styles.body}>
        <div>
          <p className={styles.label}>{label}</p>
          <p className={styles.value}>{value}</p>
          {hint && <p className={styles.hint}>{hint}</p>}
        </div>
        {icon && (
          <span className={`${styles.icon} ${styles[`tone_${tone}`] || styles.tone_navy}`}>
            <Icon name={icon} size={22} />
          </span>
        )}
      </div>
    </Card>
  )
}
