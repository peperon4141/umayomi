/**
 * JRAレースデータのモックデータ
 * 月 → 日 → レース → レース詳細の階層構造
 */

export interface RaceDetail {
  id: string
  raceNumber: number
  raceName: string
  grade: string
  distance: number
  surface: string
  age: string
  weight: string
  prize: number
  startTime: string
  venue: string
  description: string
  horses: Horse[]
}

export interface Horse {
  id: string
  number: number
  name: string
  jockey: string
  trainer: string
  weight: number
  odds: number
  age: number
  sex: string
  color: string
}

export interface Race {
  id: string
  raceNumber: number
  raceName: string
  grade: string
  distance: number
  surface: string
  startTime: string
  venue: string
  prize: number
  description: string
}

export interface RaceDay {
  id: string
  date: string
  venue: string
  races: Race[]
}

export interface RaceMonth {
  id: string
  year: number
  month: number
  name: string
  days: RaceDay[]
}

// モックデータ
export const mockRaceMonths: RaceMonth[] = [
  {
    id: '2024-10',
    year: 2024,
    month: 10,
    name: '2024年10月',
    days: [
      {
        id: '2024-10-04',
        date: '2024年10月4日（金）',
        venue: '東京競馬場',
        races: [
          {
            id: 'race-1',
            raceNumber: 1,
            raceName: '2歳未勝利',
            grade: '未勝利',
            distance: 1600,
            surface: 'ダート',
            startTime: '10:05',
            venue: '東京',
            prize: 500000,
            description: '2歳未勝利 1,600m（ダート）'
          },
          {
            id: 'race-2',
            raceNumber: 2,
            raceName: '2歳未勝利',
            grade: '未勝利',
            distance: 2000,
            surface: '芝',
            startTime: '10:35',
            venue: '東京',
            prize: 500000,
            description: '2歳未勝利 2,000m（芝）'
          },
          {
            id: 'race-3',
            raceNumber: 3,
            raceName: '2歳新馬',
            grade: '新馬',
            distance: 1400,
            surface: '芝',
            startTime: '11:05',
            venue: '東京',
            prize: 500000,
            description: '2歳新馬 1,400m（芝）'
          },
          {
            id: 'race-4',
            raceNumber: 4,
            raceName: '障害3歳以上オープン',
            grade: 'オープン',
            distance: 3100,
            surface: 'ダート',
            startTime: '11:35',
            venue: '東京',
            prize: 1000000,
            description: '障害3歳以上オープン 3,100m（ダート）別定'
          },
          {
            id: 'race-5',
            raceNumber: 5,
            raceName: '2歳新馬',
            grade: '新馬',
            distance: 1800,
            surface: '芝',
            startTime: '12:25',
            venue: '東京',
            prize: 500000,
            description: '2歳新馬 1,800m（芝）'
          },
          {
            id: 'race-6',
            raceNumber: 6,
            raceName: '3歳以上1勝クラス',
            grade: '1勝クラス',
            distance: 1400,
            surface: 'ダート',
            startTime: '12:55',
            venue: '東京',
            prize: 800000,
            description: '3歳以上1勝クラス 1,400m（ダート）定量'
          },
          {
            id: 'race-7',
            raceNumber: 7,
            raceName: '3歳以上1勝クラス',
            grade: '1勝クラス',
            distance: 2000,
            surface: '芝',
            startTime: '13:25',
            venue: '東京',
            prize: 800000,
            description: '3歳以上1勝クラス 2,000m（芝）（牝）定量'
          },
          {
            id: 'race-8',
            raceNumber: 8,
            raceName: '3歳以上1勝クラス',
            grade: '1勝クラス',
            distance: 1600,
            surface: 'ダート',
            startTime: '13:55',
            venue: '東京',
            prize: 800000,
            description: '3歳以上1勝クラス 1,600m（ダート）定量'
          },
          {
            id: 'race-9',
            raceNumber: 9,
            raceName: '八ヶ岳特別',
            grade: '2勝クラス',
            distance: 1800,
            surface: '芝',
            startTime: '14:30',
            venue: '東京',
            prize: 1200000,
            description: '八ヶ岳特別 3歳以上2勝クラス 1,800m（芝）定量'
          },
          {
            id: 'race-10',
            raceNumber: 10,
            raceName: 'エクセル田無開設30周年記念白秋ステークス',
            grade: '3勝クラス',
            distance: 1400,
            surface: '芝',
            startTime: '15:05',
            venue: '東京',
            prize: 1500000,
            description: 'エクセル田無開設30周年記念白秋ステークス 3歳以上3勝クラス 1,400m（芝）ハンデ'
          },
          {
            id: 'race-11',
            raceNumber: 11,
            raceName: '開局30周年記念グリーンチャンネルカップ',
            grade: 'オープン',
            distance: 1600,
            surface: 'ダート',
            startTime: '15:45',
            venue: '東京',
            prize: 2000000,
            description: '開局30周年記念グリーンチャンネルカップ（L） 3歳以上オープン 1,600m（ダート）別定'
          },
          {
            id: 'race-12',
            raceNumber: 12,
            raceName: '3歳以上2勝クラス',
            grade: '2勝クラス',
            distance: 1400,
            surface: 'ダート',
            startTime: '16:25',
            venue: '東京',
            prize: 1200000,
            description: '3歳以上2勝クラス 1,400m（ダート）定量'
          }
        ]
      },
      {
        id: '2024-10-05',
        date: '2024年10月5日（土）',
        venue: '京都競馬場',
        races: [
          {
            id: 'race-13',
            raceNumber: 1,
            raceName: '2歳未勝利',
            grade: '未勝利',
            distance: 1400,
            surface: 'ダート',
            startTime: '10:05',
            venue: '京都',
            prize: 500000,
            description: '2歳未勝利 1,400m（ダート）'
          },
          {
            id: 'race-14',
            raceNumber: 2,
            raceName: '2歳未勝利',
            grade: '未勝利',
            distance: 1800,
            surface: '芝',
            startTime: '10:35',
            venue: '京都',
            prize: 500000,
            description: '2歳未勝利 1,800m（芝）'
          },
          {
            id: 'race-15',
            raceNumber: 3,
            raceName: '2歳未勝利',
            grade: '未勝利',
            distance: 1400,
            surface: '芝',
            startTime: '11:05',
            venue: '京都',
            prize: 500000,
            description: '2歳未勝利 1,400m（芝）'
          },
          {
            id: 'race-16',
            raceNumber: 4,
            raceName: '障害3歳以上未勝利',
            grade: '未勝利',
            distance: 3000,
            surface: 'ダート',
            startTime: '11:35',
            venue: '京都',
            prize: 500000,
            description: '障害3歳以上未勝利 3,000m（ダート）定量'
          },
          {
            id: 'race-17',
            raceNumber: 5,
            raceName: '2歳新馬',
            grade: '新馬',
            distance: 2000,
            surface: '芝',
            startTime: '12:25',
            venue: '京都',
            prize: 500000,
            description: '2歳新馬 2,000m（芝）'
          },
          {
            id: 'race-18',
            raceNumber: 6,
            raceName: '2歳新馬',
            grade: '新馬',
            distance: 1600,
            surface: 'ダート',
            startTime: '12:55',
            venue: '京都',
            prize: 500000,
            description: '2歳新馬 1,600m（ダート）'
          },
          {
            id: 'race-19',
            raceNumber: 7,
            raceName: '3歳以上1勝クラス',
            grade: '1勝クラス',
            distance: 1400,
            surface: '芝',
            startTime: '13:25',
            venue: '京都',
            prize: 800000,
            description: '3歳以上1勝クラス 1,400m（芝）定量'
          },
          {
            id: 'race-20',
            raceNumber: 8,
            raceName: '3歳以上1勝クラス',
            grade: '1勝クラス',
            distance: 1800,
            surface: '芝',
            startTime: '13:55',
            venue: '京都',
            prize: 800000,
            description: '3歳以上1勝クラス 1,800m（芝）定量'
          },
          {
            id: 'race-21',
            raceNumber: 9,
            raceName: 'tvk賞',
            grade: '2勝クラス',
            distance: 1400,
            surface: '芝',
            startTime: '14:30',
            venue: '京都',
            prize: 1200000,
            description: 'tvk賞 3歳以上2勝クラス 1,400m（芝）定量'
          },
          {
            id: 'race-22',
            raceNumber: 10,
            raceName: '赤富士ステークス',
            grade: '3勝クラス',
            distance: 1600,
            surface: 'ダート',
            startTime: '15:05',
            venue: '京都',
            prize: 1500000,
            description: '赤富士ステークス 3歳以上3勝クラス 1,600m（ダート）定量'
          },
          {
            id: 'race-23',
            raceNumber: 11,
            raceName: '第76回 毎日王冠',
            grade: 'GⅡ',
            distance: 1800,
            surface: '芝',
            startTime: '15:45',
            venue: '京都',
            prize: 10000000,
            description: '第76回 毎日王冠（GⅡ） 3歳以上オープン 1,800m（芝）別定'
          },
          {
            id: 'race-24',
            raceNumber: 12,
            raceName: '3歳以上2勝クラス',
            grade: '2勝クラス',
            distance: 1600,
            surface: 'ダート',
            startTime: '16:25',
            venue: '京都',
            prize: 1200000,
            description: '3歳以上2勝クラス 1,600m（ダート）定量'
          }
        ]
      },
      {
        id: '2024-10-11',
        date: '2024年10月11日（金）',
        venue: '新潟競馬場',
        races: [
          {
            id: 'race-25',
            raceNumber: 1,
            raceName: '2歳未勝利',
            grade: '未勝利',
            distance: 1600,
            surface: '芝',
            startTime: '10:05',
            venue: '新潟',
            prize: 500000,
            description: '2歳未勝利 1,600m（芝）（牝）'
          },
          {
            id: 'race-26',
            raceNumber: 2,
            raceName: '2歳未勝利',
            grade: '未勝利',
            distance: 1300,
            surface: 'ダート',
            startTime: '10:35',
            venue: '新潟',
            prize: 500000,
            description: '2歳未勝利 1,300m（ダート）'
          },
          {
            id: 'race-27',
            raceNumber: 3,
            raceName: '2歳未勝利',
            grade: '未勝利',
            distance: 1800,
            surface: '芝',
            startTime: '11:05',
            venue: '新潟',
            prize: 500000,
            description: '2歳未勝利 1,800m（芝）'
          },
          {
            id: 'race-28',
            raceNumber: 4,
            raceName: '2歳新馬',
            grade: '新馬',
            distance: 1400,
            surface: 'ダート',
            startTime: '11:35',
            venue: '新潟',
            prize: 500000,
            description: '2歳新馬 1,400m（ダート）'
          },
          {
            id: 'race-29',
            raceNumber: 5,
            raceName: '2歳新馬',
            grade: '新馬',
            distance: 1600,
            surface: '芝',
            startTime: '12:25',
            venue: '新潟',
            prize: 500000,
            description: '2歳新馬 1,600m（芝）'
          },
          {
            id: 'race-30',
            raceNumber: 6,
            raceName: '2歳新馬',
            grade: '新馬',
            distance: 1600,
            surface: 'ダート',
            startTime: '12:55',
            venue: '新潟',
            prize: 500000,
            description: '2歳新馬 1,600m（ダート）'
          },
          {
            id: 'race-31',
            raceNumber: 7,
            raceName: '3歳以上1勝クラス',
            grade: '1勝クラス',
            distance: 2000,
            surface: '芝',
            startTime: '13:25',
            venue: '新潟',
            prize: 800000,
            description: '3歳以上1勝クラス 2,000m（芝）定量'
          },
          {
            id: 'race-32',
            raceNumber: 8,
            raceName: '3歳以上1勝クラス',
            grade: '1勝クラス',
            distance: 1600,
            surface: 'ダート',
            startTime: '13:55',
            venue: '新潟',
            prize: 800000,
            description: '3歳以上1勝クラス 1,600m（ダート）（牝）定量'
          },
          {
            id: 'race-33',
            raceNumber: 9,
            raceName: '陣馬特別',
            grade: '2勝クラス',
            distance: 2400,
            surface: '芝',
            startTime: '14:30',
            venue: '新潟',
            prize: 1200000,
            description: '陣馬特別 3歳以上2勝クラス 2,400m（芝）定量'
          },
          {
            id: 'race-34',
            raceNumber: 10,
            raceName: '東村山特別',
            grade: '2勝クラス',
            distance: 2100,
            surface: 'ダート',
            startTime: '15:05',
            venue: '新潟',
            prize: 1200000,
            description: '東村山特別 3歳以上2勝クラス 2,100m（ダート）定量'
          },
          {
            id: 'race-35',
            raceNumber: 11,
            raceName: '日本・サウジアラビア外交関係樹立70周年記念第11回 サウジアラビアロイヤルカップ',
            grade: 'GⅢ',
            distance: 1600,
            surface: '芝',
            startTime: '15:45',
            venue: '新潟',
            prize: 5000000,
            description: '日本・サウジアラビア外交関係樹立70周年記念第11回 サウジアラビアロイヤルカップ（GⅢ） 2歳オープン 1,600m（芝）'
          },
          {
            id: 'race-36',
            raceNumber: 12,
            raceName: '3歳以上1勝クラス',
            grade: '1勝クラス',
            distance: 1400,
            surface: 'ダート',
            startTime: '16:25',
            venue: '新潟',
            prize: 800000,
            description: '3歳以上1勝クラス 1,400m（ダート）定量'
          }
        ]
      }
    ]
  }
]

// レース詳細のモックデータ
export const mockRaceDetails: { [key: string]: RaceDetail } = {
  'race-1': {
    id: 'race-1',
    raceNumber: 1,
    raceName: '2歳未勝利',
    grade: '未勝利',
    distance: 1600,
    surface: 'ダート',
    age: '2歳',
    weight: '54kg',
    prize: 500000,
    startTime: '10:05',
    venue: '東京',
    description: '2歳未勝利 1,600m（ダート）',
    horses: [
      {
        id: 'horse-1',
        number: 1,
        name: 'サンプルホース1',
        jockey: '田中太郎',
        trainer: '佐藤一郎',
        weight: 54,
        odds: 3.2,
        age: 2,
        sex: '牡',
        color: '鹿毛'
      },
      {
        id: 'horse-2',
        number: 2,
        name: 'サンプルホース2',
        jockey: '山田花子',
        trainer: '鈴木二郎',
        weight: 54,
        odds: 5.8,
        age: 2,
        sex: '牝',
        color: '栗毛'
      },
      {
        id: 'horse-3',
        number: 3,
        name: 'サンプルホース3',
        jockey: '高橋三郎',
        trainer: '田村三郎',
        weight: 54,
        odds: 2.1,
        age: 2,
        sex: '牡',
        color: '青鹿毛'
      }
    ]
  },
  'race-23': {
    id: 'race-23',
    raceNumber: 11,
    raceName: '第76回 毎日王冠',
    grade: 'GⅡ',
    distance: 1800,
    surface: '芝',
    age: '3歳以上',
    weight: '58kg',
    prize: 10000000,
    startTime: '15:45',
    venue: '京都',
    description: '第76回 毎日王冠（GⅡ） 3歳以上オープン 1,800m（芝）別定',
    horses: [
      {
        id: 'horse-4',
        number: 1,
        name: 'スターライト',
        jockey: '武豊',
        trainer: '藤田伸二',
        weight: 58,
        odds: 2.8,
        age: 4,
        sex: '牡',
        color: '鹿毛'
      },
      {
        id: 'horse-5',
        number: 2,
        name: 'サンダーボルト',
        jockey: '川田将雅',
        trainer: '友道康夫',
        weight: 58,
        odds: 4.2,
        age: 5,
        sex: '牡',
        color: '栗毛'
      },
      {
        id: 'horse-6',
        number: 3,
        name: 'ウィンドストーム',
        jockey: '松若風馬',
        trainer: '池江泰寿',
        weight: 58,
        odds: 6.5,
        age: 4,
        sex: '牡',
        color: '青鹿毛'
      }
    ]
  }
}
